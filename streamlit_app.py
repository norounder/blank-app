import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re 
import warnings
import gspread # gspread 라이브러리 추가

warnings.filterwarnings('ignore', category=FutureWarning)

st.set_page_config(layout="wide")
st.title('📖 경건 시트 데이터 분석 대시보드')

# **중요: 여기에 Google Sheets 문서의 ID를 붙여넣으세요.**
# URL에서 'd/'와 '/edit' 사이에 있는 문자열입니다.
# 예: https://docs.google.com/spreadsheets/d/ 이 부분 /edit...
SPREADSHEET_ID = '1mBwIdifaAgZN107f0lYz2i-WvoPBwesSqkzCNtUOX2U' 
SHEET_NAME = '경건시트' # 데이터를 불러올 시트의 이름

# 1. 데이터 불러오기 (Google Sheets API 사용)
@st.cache_data(ttl=600) # 10분(600초)마다 데이터를 새로고침
def load_data_from_gspread():
    try:
        # st.secrets에서 서비스 계정 정보를 가져와 인증
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        
        # 스프레드시트 열기
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        # 특정 시트 열기
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        
        # 모든 데이터를 DataFrame으로 변환
        df_raw = pd.DataFrame(worksheet.get_all_records())
        
        # 제공된 헤더로 컬럼명 명확히 지정
        df_raw.columns = [
            'Timestamp', 
            'Participant', 
            'Attendance_Text', 
            'Chapter_Count_Text', 
            'Chapter_Range_Text', 
            'Days_Text', 
            'Final_Value_Text'
        ]
        
        # 값이 없는 행(데이터가 없는 행) 제거
        df_raw = df_raw.dropna(subset=['Participant']).reset_index(drop=True)
        
        return df_raw
    except Exception as e:
        st.error(f"Google Sheets API 로드 중 오류가 발생했습니다. secrets.toml 설정과 스프레드시트 공유 권한을 확인하세요. 오류: {e}")
        return pd.DataFrame()

df_raw = load_data_from_gspread() 

if not df_raw.empty:
    # ... (이하 데이터 정리 및 시각화 코드는 동일합니다) ...
    # 2. Google Sheets 수식을 Pandas로 변환하여 데이터 정리
    
    df = pd.DataFrame()
    
    # 2-1. Date: 날짜 형식 변환
    df['Date'] = pd.to_datetime(df_raw['Timestamp']).dt.strftime('%Y-%m-%d')
    
    # 2-2. Participant: 참여자 이름 정리
    df['Participant'] = df_raw['Participant'].astype(str).str.strip()
    
    # 2-3. Attended: 참석 여부 (1/0)
    df['Attended'] = df_raw['Attendance_Text'].astype(str).str.contains('참석', na=False).astype(int)
    
    # 2-4. Chapter_Count: QT 횟수에서 숫자 추출
    df['Chapter_Count'] = df_raw['Chapter_Count_Text'].astype(str).str.extract('(\d+)').astype(float).fillna(0)
    
    # 2-5. Chapter_End: 말씀 읽기에서 마지막 숫자 추출 (룩업 로직 대체)
    # 예: '13~15장' -> '15'
    df['Chapter_End'] = df_raw['Chapter_Range_Text'].astype(str).str.extract(r'(\d+)\D*$').astype(float).fillna(0)

    # 2-6. Days: 기도에서 숫자 추출 (일당)
    df['Days'] = df_raw['Days_Text'].astype(str).str.extract('(\d+)').astype(float).fillna(0)
    
    # 2-7. Final_Value: 경건비는 얼마인가요?? (마지막 값, 숫자 추출 및 0 처리)
    df['Final_Value'] = df_raw['Final_Value_Text'].astype(str).str.replace(r'[^\d]', '', regex=True).replace('', '0').astype(float)
    
    # 최종 데이터 확인
    st.subheader('🚀 데이터 클리닝 결과 (최근 5건)')
    st.dataframe(df.tail())

    # --- 데이터 분석 및 시각화 ---
    
    # 3. 참여자 선택 필터 (사이드바)
    all_participants = ['전체'] + sorted(df['Participant'].unique().tolist())
    selected_participant = st.sidebar.selectbox('참여자 선택', all_participants)

    if selected_participant != '전체':
        df_filtered = df[df['Participant'] == selected_participant].copy()
        st.subheader(f"👤 **{selected_participant}** 님의 누적 데이터")
    else:
        df_filtered = df.copy()
        st.subheader("👥 전체 참여자 누적 데이터")
    
    st.markdown('---')
    
    # A. 참여자별 누적 참석 횟수 (전체 참여자 대상)
    if selected_participant == '전체':
        st.markdown('### 참여자별 총 참석 횟수')
        attendance_counts = df.groupby('Participant')['Attended'].sum().sort_values(ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        attendance_counts.plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title('참여자별 총 참석 횟수')
        ax.set_ylabel('총 횟수 (참석:1)')
        ax.set_xlabel('참여자 이름')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
        
        st.markdown('---')
    
    # B. 시간 경과에 따른 누적 경건비 추이
    st.markdown('### 시간 경과에 따른 누적 경건비 추이')
    
    # 누적 금액 계산
    df_plot = df_filtered.copy()

    if selected_participant == '전체':
        # 전체일 경우 참여자별로 누적 금액 계산
        df_plot['Cumulative_Value'] = df_plot.groupby('Participant')['Final_Value'].cumsum()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        for name, group in df_plot.groupby('Participant'):
            ax.plot(group['Date'], group['Cumulative_Value'], label=name)
        
        ax.set_title('참여자별 누적 경건비 추이')
        ax.legend(title='참여자', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.set_ylabel('누적 금액 (원)')
        ax.set_xlabel('날짜')
        plt.tight_layout()
        st.pyplot(fig)
        
    else:
        # 특정 참여자라면, 해당 참여자의 누적 합계만 계산
        df_plot['Cumulative_Value'] = df_plot['Final_Value'].cumsum()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df_plot['Date'], df_plot['Cumulative_Value'], marker='o', color='green')
        ax.set_title(f"{selected_participant} 님의 누적 경건비 추이")
        ax.set_ylabel('누적 금액 (원)')
        ax.set_xlabel('날짜')
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)