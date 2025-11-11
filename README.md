# 📖 경건 시트 데이터 분석 대시보드 (Streamlit App)

이 프로젝트는 Google Sheets에 기록된 경건 활동 데이터를 실시간으로 불러와 **참여자별 활동 및 경건비 추이를 시각화**하는 Streamlit 대시보드 애플리케이션입니다.

---

## 🚀 1. 앱 실행을 위한 환경 설정

이 앱을 정상적으로 실행하고 Google Sheets 데이터를 불러오려면, **보안 설정 파일**을 구성해야 합니다.

### 1.1. `secrets.toml` 파일 생성 (필수)

**절대 외부에 공개되어서는 안 되는 민감한 정보**가 포함되므로, GitHub에 올라와 있는 `secrets.example.toml` 파일을 참고하여 **`.streamlit/secrets.toml`** 파일을 **직접 생성**해야 합니다.

```bash
cp secrets.example.toml .streamlit/secrets.toml
```

### 1.2. `secrets.toml` 설정 채우기

생성한 `.streamlit/secrets.toml` 파일을 열어 다음 세 섹션의 값을 채워 넣으세요.

#### 1) `[gcp_service_account]` (Google Sheets API 연동)

Google Sheets 데이터에 접근하기 위한 **서비스 계정 키 정보**입니다.

* Google Cloud Platform에서 **서비스 계정**을 생성합니다.
* 생성된 계정의 **JSON 키 파일**을 다운로드합니다.
* JSON 파일의 내용을 복사하여 각 필드에 붙여넣습니다.
    * **중요:** 특히 `private_key`는 **줄바꿈(`\n`)을 포함한 전체 문자열**을 넣어야 합니다.
* **필수:** 해당 서비스 계정 이메일 주소에 분석할 Google Sheet의 **읽기 권한**을 반드시 부여해야 합니다.

#### 2) `[spread_sheet]` (시트 정보)

분석 대상 시트의 정보를 입력합니다.

| 키 | 설명 | 예시 |
| :--- | :--- | :--- |
| `spreadsheet_id` | 분석할 Google Sheet URL에서 `d/`와 `/edit` 사이에 있는 **고유 ID**입니다. | `1B0xxxxxxxxxxxxxxxxxB0` |
| `sheet_name` | 데이터가 기록된 시트의 **탭 이름**입니다. | `2024년 경건 활동` |

#### 3) `[name_correction_map]` 및 `[name_alias_map]` (이름 관리)

데이터 일관성을 유지하고 개인 정보 노출 없이 사용할 수 있도록 이름을 매핑합니다.

* **`[name_correction_map]`**: 시트에 오타가 있거나 이름 형태가 다른 경우, **정식 이름으로 통일**합니다.
    ```toml
    # "시트의 오타 이름" = "통일할 정식 이름"
    "홍길둥" = "홍길동"
    ```
* **`[name_alias_map]`**: 정식 이름을 대시보드에 표시할 **별명으로 변경**합니다. (**선택 사항**)
    ```toml
    # "정식 이름" = "대시보드 표시 별명"
    "김철수" = "철수님"
    ```

---

## 💻 2. 설치 및 실행

### 2.1. 라이브러리 설치

프로젝트 루트에 있는 `requirements.txt` 파일을 사용하여 필요한 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

### 2.2. 앱 실행

로컬 환경에서 앱을 실행합니다.

```bash
streamlit run streamlit_app.py 
# (혹은 파일 이름에 맞게 streamlit_app.py를 변경하세요)
```

---

## 📝 3. 코드 정보

* **한글 폰트:** `NanumGothic.ttf` 파일이 앱이 실행되는 환경(루트 폴더)에 있어야 합니다.
* **캐싱:** 데이터 로드는 `st.cache_data(ttl=600)`로 캐싱되어 **10분마다** 시트의 최신 데이터를 가져옵니다.
