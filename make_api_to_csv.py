import requests
import pprint
import json
import pandas as pd
import os

filePath, fileName = os.path.split(__file__)

'''NEWS API'''
def flood_news(HydroType, DataType,Edt, DocumentType):
        url = f'http://223.130.129.189:9191/{HydroType}/{DataType}/{Edt}{DocumentType}'
        response = requests.get(url)
        contents = response.text
        json_ob = json.loads(contents)
        body = json_ob['content']
        body = pd.json_normalize(body)
        return body




'''홍수관련 실시간 정보 API'''
def floodsiteAPI_livedata(HydroType, DataType, time = None, DocumentType = None):
    if DataType == 'list':
        url = f'http://223.130.129.189:9191/{HydroType}/{DataType}/{time}{DocumentType}'
    elif DataType == 'info':
        url = f'http://223.130.129.189:9191/{HydroType}/{DataType}{DocumentType}'
    response = requests.get(url)
    contents = response.text
    json_ob = json.loads(contents)
    body = json_ob['content']
    body = pd.json_normalize(body)
    return body





'''실시간 초단기 기상정보 API'''
def weatherData():
    # 시간 설정
    base_datebf30 = datetime.now() + timedelta(hours = 9) - timedelta(minutes = 30)
    base_date = base_datebf30.strftime('%Y%m%d')
    if int(base_datebf30.strftime('%d')) > 30:
        base_time = base_datebf30.strftime('%H00')
    else :
        base_time = base_datebf30.strftime('%H30')

    # api 호출준비(지역별 대기값)
    korea_xy_df = pd.read_csv(data_path)

    # 지역 선택
    cd_nm_list = list(korea_xy_df['1단계'].unique())
    cd_nm = st.selectbox('시도 선택',cd_nm_list)

    sgg_nm_list = list(korea_xy_df[korea_xy_df['1단계'] == cd_nm]['2단계'].unique())
    sgg_nm = st.selectbox('시군구 선택',sgg_nm_list)

    # 격자 X, 격자 Y값 찾기
    korea_xy_df = korea_xy_df[(korea_xy_df['1단계'] == cd_nm) & (korea_xy_df['2단계'] == sgg_nm)]
    nx = korea_xy_df.iloc[0,2]
    ny = korea_xy_df.iloc[0,3]

    # api 호출
    url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
    params ={'serviceKey' : '3ouN4EKp4qGz+V76EbDHKehnbp5sYL0o19tpl5fAl2Q7s4ZosClGRfc1ENwk+2Px4QUPi4gCuCHGuG3kXFrs9w==',
            'pageNo' : '1', 'numOfRows' : '1000', 'dataType' : 'JSON', 'base_date' : base_date, 'base_time' : base_time, 'nx' : nx, 'ny' : ny }

    # json csv 변환
    response = requests.get(url, params=params)
    contents = response.content
    json_ob = json.loads(contents)
    body = json_ob['response']['body']['items']['item']
    body = pd.json_normalize(body)

    # 데이터 나누기
    temperature = body[body['category'] == 'T1H'].reset_index(drop = True)
    raining = body[body['category'] == 'RN1'].reset_index(drop = True)
    sky = body[body['category'] == 'SKY'].reset_index(drop = True)
    shape_rn = body[body['category'] == 'PTY'].reset_index(drop = True)
    humidity = body[body['category'] == 'REH'].reset_index(drop = True)
    thunder = body[body['category'] == 'LGT'].reset_index(drop = True)
    windspeed = body[body['category'] == 'WSD'].reset_index(drop = True)

    return cd_nm, sgg_nm, temperature, raining, sky, shape_rn, humidity, thunder, windspeed





'''지진해일 대피소 정보 API'''
def TsunamiShelter():
    pageNo = 1
    numOfRows = 1000
    type = 'json'
    url = f'http://223.130.129.189:9191/getTsunamiShelter1List/numOfRows={numOfRows}&pageNo={pageNo}&type={type}'
    response = requests.get(url)
    json_ob = json.loads(response.content)
    body = json_ob['TsunamiShelter'][1]['row']
    body = pd.json_normalize(body)
    return body





'''임시주거시설 정보 API'''
def temporary_house():
    vin_df = pd.DataFrame()
    pageNo = 1
    while pageNo <= 16:
            pageNo = str(pageNo)
            url = 'http://apis.data.go.kr/1741000/TemporaryHousingFacilityVictim3/getTemporaryHousingFacilityVictim1List'
            params ={'serviceKey' : '3ouN4EKp4qGz+V76EbDHKehnbp5sYL0o19tpl5fAl2Q7s4ZosClGRfc1ENwk+2Px4QUPi4gCuCHGuG3kXFrs9w==',
                    'pageNo' : pageNo,
                    'numOfRows' : '1000',
                    'type' : 'json' }

            response = requests.get(url, params=params)
            contents = response.text
            json_ob = json.loads(contents)
            body = json_ob['TemporaryHousingFacilityVictim'][1]['row']
            body = pd.json_normalize(body)
            vin_df = pd.concat([vin_df,body], axis = 0)
            pageNo = int(pageNo) + 1
            
    columns = ['ctprvn_nm', 'sgg_nm', 'acmdfclty_se_nm', 'vt_acmdfclty_nm', 'dtl_adres', 'fclty_ar', 'vt_acmd_psbl_nmpr', 'mngps_nm', 'mngps_telno', 'xcord', 'ycord']
    vin_df2 = vin_df[columns]
    vin_df2.columns = ['시도명', '시군구명', '시설구분', '시설명', '상세주소','시설면적', '주거능력','관리부서','지자체담당자연락처', '경도', '위도']
    vin_df2.reset_index(drop = True).to_csv(os.path.join(filePath, 'pages','using_data', 'temporary_house.csv'), index = False, encoding = 'utf-8-sig')





'''긴급구호물자 구매업체 API'''
def save_items(df, path):
    df = pd.read_csv(path)
    df['시도명'] = df['주소'].str.split(' ').str[0]
    df['시군구명'] = df['주소'].str.split(' ').str[1]
    df.to_csv(os.path.join(filePath, 'pages', 'using_data', '구호물자정보.csv'), index = False, encoding = 'utf-8-sig')






'''응급의료기관 정보 실시간 조회 API'''
def emergency_hospital(cd_nm, sgg_nm):

        # 공공데이터 조회
        url = 'http://apis.data.go.kr/B552657/ErmctInfoInqireService/getEmrrmRltmUsefulSckbdInfoInqire'
        params ={'serviceKey' : '3ouN4EKp4qGz+V76EbDHKehnbp5sYL0o19tpl5fAl2Q7s4ZosClGRfc1ENwk+2Px4QUPi4gCuCHGuG3kXFrs9w==', 'STAGE1' : cd_nm, 'STAGE2' : sgg_nm, 'pageNo' : '1', 'numOfRows' : '1000' }

        response = requests.get(url, params=params)
        content = response.text

        ### xml을 DataFrame으로 변환하기 ###
        #bs4 사용하여 item 태그 분리

        xml_obj = bs4.BeautifulSoup(content,'lxml-xml')
        rows = xml_obj.findAll('item')

        # 각 행의 컬럼, 이름, 값을 가지는 리스트 만들기
        row_list = [] # 행값
        name_list = [] # 열이름값
        value_list = [] #데이터값

        # xml 안의 데이터 수집
        for i in range(0, len(rows)):
            columns = rows[i].find_all()
            #첫째 행 데이터 수집
            for j in range(0,len(columns)):
                if i ==0:
                    # 컬럼 이름 값 저장
                    name_list.append(columns[j].name)
                # 컬럼의 각 데이터 값 저장
                value_list.append(columns[j].text)
            # 각 행의 value값 전체 저장
            row_list.append(value_list)
            # 데이터 리스트 값 초기화
            value_list=[]

        # xml값 DataFrame으로 만들기
        emergency_hospital_df = pd.DataFrame(row_list, columns=name_list)

        # 데이터 가공
        emergency_hospital_df = emergency_hospital_df[['hvidate','hvec','hvoc','hvgc','hvamyn','dutyName','dutyTel3']]
        emergency_hospital_df.columns = ['정보 업데이트 일시','응급실 가용현황', '수술실 가용현황', '입원실 가용현황', '구급차 가용여부', '기관명', '연락처']
        return emergency_hospital_df