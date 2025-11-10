import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import re 
import gspread 
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

st.set_page_config(layout="wide")
st.title('📖 경건 시트 데이터 분석 대시보드')

# --- 폰트 설정 (이전 문제 해결 코드) ---
FONT_PATH = 'NanumGothic.ttf' 

try:
    fm.fontManager.addfont(FONT_PATH)
    font_name = fm.FontProperties(fname=FONT_PATH).get_name()
    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False 
    
except Exception as e:
    st.error(f"폰트 설정 중 오류 발생. 기본 폰트로 대체됩니다. 오류: {e}")
    plt.rc('font', family='sans-serif')


# --- Google Sheets API 설정 ---
SPREADSHEET_ID = '1mBwIdifaAgZN107f0lYz2i-WvoPBwesSqkzCNtUOX2U' 
SHEET_NAME = '경건시트' 

@st.cache_data(ttl=600) 
def load_data_from_gspread():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        df_raw = pd.DataFrame(worksheet.get_all_records())
        
        df_raw.columns = [
            'Timestamp', 
            'Participant', 
            'Attendance_Text', 
            'Chapter_Count_Text', 
            'Chapter_Range_Text', 
            'Days_Text', 
            'Final_Value_Text'
        ]
        
        df_raw = df_raw.dropna(subset=['Participant']).reset_index(drop=True)
        return df_raw
    except Exception as e:
        st.error(f"Google Sheets API 로드 중 오류가 발생했습니다. secrets 설정과 공유 권한을 확인하세요. 오류: {e}")
        return pd.DataFrame()

df_raw = load_data_from_gspread() 

if not df_raw.empty:
    
    # --- 데이터 정리 및 변환 ---
    df = pd.DataFrame()
    TIME_FORMAT = '%Y. %m. %d' 
    
    # 1. 날짜 변환 및 오류 처리
    df['Date_Time'] = pd.to_datetime(df_raw['Timestamp'], format=TIME_FORMAT, errors='coerce')
    df = df.dropna(subset=['Date_Time']).copy() 
    df['Date'] = df['Date_Time'].dt.strftime('%Y-%m-%d')
    
    # 2. 참여자 정리
    df['Participant'] = df_raw['Participant'].astype(str).str.strip()
    
    # 3. 항목별 데이터 추출 및 정리
    df['Attendance'] = df_raw['Attendance_Text'].astype(str).str.contains('참석', na=False).astype(int)
    df['QT_Count'] = df_raw['Chapter_Count_Text'].astype(str).str.extract('(\d+)').astype(float).fillna(0)
    df['Chapter_Reading'] = df_raw['Chapter_Range_Text'].astype(str).str.extract(r'(\d+)\D*$').astype(float).fillna(0)
    df['Prayer_Count'] = df_raw['Days_Text'].astype(str).str.extract('(\d+)').astype(float).fillna(0)
    # 정규표현식을 사용하여 숫자만 추출하고, 빈 문자열을 '0'으로 대체 후 float 변환
    df['Devotion_Fee'] = df_raw['Final_Value_Text'].astype(str).str.replace(r'[^\d]', '', regex=True).replace('', '0').astype(float)
    
    # --- UI 및 필터 ---
    
    st.sidebar.header('분석 대상 선택')
    
    all_participants = sorted(df['Participant'].unique().tolist())
    
    selected_participant = st.sidebar.selectbox('참여자 선택', all_participants)

    if not selected_participant:
         st.warning("경고: 스프레드시트에 유효한 참여자 이름이 없습니다.")
         st.stop()
    
    # --- 필터링 및 일별 합산 ---
    df_filtered = df[df['Participant'] == selected_participant].copy()
    
    # 일별 데이터를 보여주기 위해, 해당 날짜에 여러 항목이 기록된 경우를 대비하여 날짜별로 그룹화하여 합산합니다.
    df_filtered_daily = df_filtered.groupby('Date').agg({
        'Attendance': 'sum',
        'QT_Count': 'sum',
        'Chapter_Reading': 'sum',
        'Prayer_Count': 'sum',
        'Devotion_Fee': 'sum'
    }).reset_index()
    
    st.header(f"👤 **{selected_participant}** 님 활동 분석 (일별)")
    
    if df_filtered_daily.empty:
        st.warning(f"경고: {selected_participant} 님의 데이터가 스프레드시트에서 발견되지 않았습니다.")
        st.stop()

    # --- 그래프 1: 활동 기록 추이 (Attendance, QT, Reading, Prayer) ---
    
    st.subheader('1. 활동 기록 일별 추이 (참석, QT, 읽기, 기도)')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df_filtered_daily['Date'], df_filtered_daily['Attendance'], label='참석 (1/0)', marker='o', linestyle='--')
    ax.plot(df_filtered_daily['Date'], df_filtered_daily['QT_Count'], label='QT 횟수', marker='s')
    ax.plot(df_filtered_daily['Date'], df_filtered_daily['Chapter_Reading'], label='말씀 읽기 장수', marker='^')
    ax.plot(df_filtered_daily['Date'], df_filtered_daily['Prayer_Count'], label='기도 횟수', marker='x')
    
    # QT_Count에 레이블 추가 (소수점 없이 정수로 표시)
    for i, row in df_filtered_daily.iterrows():
        if row['QT_Count'] > 0: # 0이 아닌 값만 표시하여 그래프를 덜 복잡하게 유지
            ax.text(
                row['Date'], 
                row['QT_Count'], 
                f"{int(row['QT_Count'])}회", 
                fontsize=9, 
                ha='center', 
                va='bottom',
                color='darkblue'
            )
        if row['Chapter_Reading'] > 0: # 0이 아닌 값만 표시하여 그래프를 덜 복잡하게 유지
            ax.text(
                row['Date'], 
                row['Chapter_Reading'], 
                f"{int(row['Chapter_Reading'])}장", 
                fontsize=9, 
                ha='center', 
                va='bottom',
                color='darkblue'
            )
        if row['Prayer_Count'] > 0: # 0이 아닌 값만 표시하여 그래프를 덜 복잡하게 유지
            ax.text(
                row['Date'], 
                row['Prayer_Count'], 
                f"{int(row['Prayer_Count'])}회", 
                fontsize=9, 
                ha='center', 
                va='bottom',
                color='darkblue'
            )
            
    ax.set_title(f"{selected_participant} 님의 주요 활동 일별 추이")
    ax.set_xlabel('날짜')
    ax.set_ylabel('일별 값')
    ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig)

    st.markdown('---')

    # --- 그래프 2: 경건비 추이 (Devotion Fee) ---
    
    st.subheader('2. 경건비 일별 값 추이')
    
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    
    # 일별 값으로 변경
    ax2.plot(df_filtered_daily['Date'], df_filtered_daily['Devotion_Fee'], 
             label='일별 경건비', marker='D', color='green', linewidth=2)
             
    # Devotion_Fee에 레이블 추가 (콤마와 '원' 단위로 표시)
    for i, row in df_filtered_daily.iterrows():
        if row['Devotion_Fee'] > 0: # 0이 아닌 값만 표시
            ax2.text(
                row['Date'], 
                row['Devotion_Fee'], 
                f"{int(row['Devotion_Fee']):,}원", # 천 단위 콤마 추가
                fontsize=9, 
                ha='center', 
                va='bottom',
                color='red'
            )
    
    ax2.set_title(f"{selected_participant} 님의 일별 경건비 추이")
    ax2.set_xlabel('날짜')
    ax2.set_ylabel('일별 금액 (원)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    st.pyplot(fig2)