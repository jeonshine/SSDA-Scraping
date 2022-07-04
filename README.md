# SSDA-Scraping

+ SSDA : Same Source Different Article

        수능과 모의고사에 출제된 문제의 문장을 검색해
        원전(source)을 찾아 데이터를 긁어오는 프로젝트입니다.

+ 출처 : [구글북스](https://books.google.co.kr/)
+ 기록 : [스프레드 시트](https://docs.google.com/spreadsheets/d/1LXdeLdZl7niJgd9z0H-S_bjlLEudR2-hMpindc1G0ww/edit#gid=0)
  - 스프레드 시트 이름 : SSDA Scrapping Tool 
  - 데이터 입력 시트 이름 : 데이터 입력
+ 수집 데이터
  - 원전 제목  
  - 원전 저자 
  - 원전에서 검색된 문장 
  - 원전 구글북스 주소 
  - 원전 표지 
  - 원전에서 검색된 페이지 
  - 원전의 전체 페이지 
  - 원전의 전체 페이지 수
        
+ 사용 라이브러리 : selenium, gspread
        
+ 수집 방법
  1. 아래와 같이 스프레드 시트에 첫 번째 문장과 두 번째 문장을 입력합니다.
  ![image](https://user-images.githubusercontent.com/105637993/177030725-a7cbea5d-0d33-4222-af8f-995c5e732c21.png)

  2. 소스코드를 실행하면 다음과 같은 시트가 생성됩니다.
  ![image](https://user-images.githubusercontent.com/105637993/177030767-4796a936-8c56-46e5-a746-9d89f4ab2be0.png)
