import streamlit as st
import hydralit_components as hc
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
import os
from PIL import Image
from pytz import timezone
from datetime import datetime, timedelta
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import bs4


filePath, fileName = os.path.split(__file__)

def flood_news(HydroType, DataType,Edt, DocumentType):
        url = f'http://223.130.129.189:9191/{HydroType}/{DataType}/{Edt}{DocumentType}'
        response = requests.get(url)
        contents = response.text
        json_ob = json.loads(contents)
        body = json_ob['content']
        body = pd.json_normalize(body)
        return body

def home():
    try :

        #### 페이지 헤더, 서브헤더 제목 설정
        # 헤더
        st.header("⛔홍수 특보 발령사항")

        HydroType = 'getFldfct'
        DataType = 'list'
        # Edt = '20220810'
        DocumentType = '.json'
        Edt = datetime.today().strftime(("%Y%m%d"))
        df = flood_news(HydroType, DataType, Edt, DocumentType).drop(columns = 'links')
        df.columns = ['발표일시','발표자','수위도달 예상일시', '예상 수위표수위', '예상 해발수위', '홍수예보 종류', '홍수예보 번호', '지점', '기존발령일시', 
                    '비고','강명','변동상황', '현재 일시', '현재 수위표수위', '현재 해발수위', '예상 일시(변동)', '예상 수위표수위(변동)', '예상 해발수위(변동)', '관측소 코드', '주의 지역', 
                    '주의 강명']

        list_ = []
        for idx in df.index:
            if df.loc[idx,'홍수예보 종류'][-2:] == '발령':
                list_.append(df.loc[idx, '주의 지역'])
        warning_message = ",".join(list_)
        st.subheader("❗" + warning_message)
        st.write("해당 지역 거주자 분들은  \n  혹시 모를 사태에 대비해주시기 바랍니다.")
        df = df.set_index(['지점', '홍수예보 종류'])
        # df[['홍수예보 종류', '강명', '변동상황', '주의지역', '주의강명']]
        st.dataframe(df)
        
        image = Image.open(os.path.join(filePath,'using_data', '홍수발생시 요령.png'))
        col1, col2 = st.columns(2)
        with col1:
            # st.image(image)
            st.video('https://www.youtube.com/watch?v=cOQEdUBpLjg')
    except :
        st.write("최근 24시간 내 발효된 홍수 특보 발령사항이 없습니다😊")
        image = Image.open(os.path.join(filePath,'using_data', '홍수발생시 요령.png'))
        col1, col2 = st.columns(2)
        with col1:
            # st.image(image)
            st.video('https://www.youtube.com/watch?v=cOQEdUBpLjg')
        st.write("해당 페이지는 웹 환경에 최적화되어 제작되었습니다😊")
        pass

# 6시쯤 API 호출 안됨
def weatherData():
    data_path = os.path.join(filePath, 'using_data','korea_weatherlocation_xy.csv')
    # 시간 설정
    base_datebf30 = datetime.now(timezone('Asia/Seoul')) - timedelta(minutes = 30)

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

def weather():

    st.write(
            """
            <style>
            [data-testid="stMetricDelta"] svg {
                display: none;
            }
            </style>
            """,
            unsafe_allow_html=True,)
                
                
    st.header("☂️실시간 초단기 기상정보")
    st.write("위치 정보 선택 후, 이후 6시간의 기상정보를 받아보세요🙏")

    cd_nm, sgg_nm, temperature, raining, sky, shape_rn, humidity, thunder, windspeed = weatherData()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    for idx in temperature.index:
        time = str(raining.loc[idx,'fcstTime'])[0:2] + "시"
        temperature_data = str(temperature.loc[idx,'fcstValue'])
        raining_data = str(raining.loc[idx,'fcstValue'])
        sky_data = str(sky.loc[idx,'fcstValue'])
        if sky_data == "1":
            sky_data = "☀️맑음"
        elif sky_data == "3":
            sky_data = "⛅구름많음"
        elif sky_data == "4":
            sky_data = "☁️흐림"
            
        shape_raining = str(shape_rn.loc[idx,'fcstValue'])
        if shape_raining == "0":
            shape_raining = " "
        elif shape_raining == "1":
            shape_raining = "비🌧️"
        elif shape_raining == "2":
            shape_raining = "비/눈🌨️"
        elif shape_raining == "3":
            shape_raining = "눈🌨️"
        elif shape_raining == "5":
            shape_raining = "빗방울🌧️"
        elif shape_raining == "6":
            shape_raining = "빗방울눈날림🌧️"
        elif shape_raining == "7":
            shape_raining = "눈날림🌨️"
            
        humidity_data = str(humidity.loc[idx,'fcstValue'])
        thunder_data = str(thunder.loc[idx,'fcstValue'])
        windspeed_data = str(windspeed.loc[idx,'fcstValue'])
        
        
        with col1:
            if idx % 6 == 0:
                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")

        with col2:
            if idx % 6 == 1:

                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")

        with col3:
            if idx % 6 == 2:
                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")

        
        with col4:
            if idx % 6 == 3:
                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")
                    
        with col5:
            if idx % 6 == 4:
                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")
                    
        with col6:
            if idx % 6 == 5:
                st.markdown(f"#### {time}")
                st.metric(sky_data, value = temperature_data + "℃", delta = "풍속 : " + windspeed_data + "m/s")
                st.metric("💧습도 : " + humidity_data + "%", value= raining_data, delta= shape_raining)
                if thunder_data != "0":
                    st.write("⚡낙뢰 " + thunder_data + "kA")
                
                
    st.write(cd_nm + " " + sgg_nm + "의 초단기 기상정보입니다. 해당 페이지는 기상청 데이터를 사용합니다😊")


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
    

def flowsite():
    water_level_live = floodsiteAPI_livedata('getWaterLevel10M', 'list', '10M', '.json')
    water_level = floodsiteAPI_livedata('getWaterLevel10M', 'info', None, '.json')
    water_level = water_level[water_level['attwl'] != ' ']
    water_level['시도명'] = water_level['addr'].str.split(' ').str[0]
    water_level['lat'] = water_level['lat'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
    water_level['lon'] = water_level['lon'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
    data = pd.merge(water_level, water_level_live, on = 'wlobscd', how = 'inner')
    data = data[data['almwl'] != ' ']
    data[['attwl', 'wrnwl', 'almwl', 'srswl', 'wl']] = data[['attwl', 'wrnwl', 'almwl', 'srswl', 'wl']].astype('float64')
    data['수위경보'] = data.apply(lambda x : '심각 수위 단계' if x['wl'] >= x['srswl']
                                                        else ('경보수위 단계' if x['wl'] >= x['almwl']
                                                        else ('주의보수위 단계' if x['wl'] >= x['wrnwl']
                                                        else ('관심수위 단계' if x['wl'] >= x['attwl'] else '정상수위 단계')))  , axis = 1)
    return data


def flow_map(data):
    m = folium.Map(
    location=[data['lat'].mean(), data['lon'].mean()],
    zoom_start= 7, width = '70%', height = '50%')
    coords = data[['lat', 'lon', 'obsnm', '수위경보', 'pfh', 'wl']]

    # marker_cluster = MarkerCluster().add_to(m)
    for idx in coords.index:
        if coords.loc[idx,'수위경보'] == "정상수위 단계":
            folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="green"), tooltip = coords.loc[idx,'obsnm']  +  '<br>현재 수위 :' + str(coords.loc[idx,'wl']) + '<br>최대 수위 :' + str(coords.loc[idx,'pfh'])).add_to(m)
        elif coords.loc[idx,'수위경보'] == "관심수위 단계":
            folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="blue"), tooltip = coords.loc[idx,'obsnm']  +  '<br>현재 수위 :' + str(coords.loc[idx,'wl']) + '<br>최대 수위 :' + str(coords.loc[idx,'pfh'])).add_to(m)
        elif coords.loc[idx,'수위경보'] == "주의보수위 단계":
            folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="orange"), tooltip = coords.loc[idx,'obsnm']  +  '<br>현재 수위 :' + str(coords.loc[idx,'wl']) + '<br>최대 수위 :' + str(coords.loc[idx,'pfh'])).add_to(m)
        elif coords.loc[idx,'수위경보'] == "경보수위 단계":
            folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="purple"), tooltip = coords.loc[idx,'obsnm']  +  '<br>현재 수위 :' + str(coords.loc[idx,'wl']) + '<br>최대 수위 :' + str(coords.loc[idx,'pfh'])).add_to(m)
        elif coords.loc[idx,'수위경보'] == "심각수위 단계":
            folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="red"), tooltip = coords.loc[idx,'obsnm']  +  '<br>현재 수위 :' + str(coords.loc[idx,'wl']) + '<br>최대 수위 :' + str(coords.loc[idx,'pfh'])).add_to(m)
    return m

 
def dam_data_make():
        livedata = floodsiteAPI_livedata('getDam10M', 'list', '1H', '.json')
        data = floodsiteAPI_livedata('getDam10M', 'info', None, '.json')
        dam_data = pd.merge(data, livedata, on = 'dmobscd', how = 'inner')
        dam_data = dam_data[dam_data['lat'] != ' ']
        dam_data = dam_data[dam_data['lon'] != ' ']
        dam_data['lat'] = dam_data['lat'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
        dam_data['lon'] = dam_data['lon'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
        return dam_data

 
def dam_map(data):
        m = folium.Map(
        location=[data['lat'].mean(), data['lon'].mean()],
        zoom_start= 7, width = '70%', height = '50%'
        )
        coords = data[['lat', 'lon', 'obsnm', 'swl', 'inf', 'sfw', 'ecpc', 'tototf']]
        for idx in coords.index:
                text = coords.loc[idx,'obsnm']+ '<br>현재 수위 :' + str(coords.loc[idx,'swl']) + '<br>유입량 :' + str(coords.loc[idx,'inf'])+ '<br>저수량 :' + str(coords.loc[idx,'sfw']) + '<br>공용량 :' + str(coords.loc[idx,'ecpc']) + '<br>총 방류량 :' + str(coords.loc[idx,'tototf'])
                folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="green"), tooltip = text).add_to(m)
        return m

 
def bo_data_make():
        livedata = floodsiteAPI_livedata('getBo10M', 'list', '1H', '.json')
        data = floodsiteAPI_livedata('getBo10M', 'info', None, '.json')
        bo_data = pd.merge(data, livedata, on = 'boobscd', how = 'inner')
        bo_data = bo_data[bo_data['lat'] != ' ']
        bo_data = bo_data[bo_data['lon'] != ' ']
        bo_data['lat'] = bo_data['lat'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
        bo_data['lon'] = bo_data['lon'].apply(lambda x : int(x.split('-')[0]) + (int(x.split('-')[1]) / 60) + (int(x.split('-')[2]) / 3600) if len(x.split('-')) == 3 else x)
        return bo_data

 
def bo_map(data):
        m = folium.Map(
        location=[data['lat'].mean(), data['lon'].mean()],
        zoom_start= 7, width = '70%', height = '50%'
        )
        coords = data[['lat', 'lon', 'obsnm', 'swl', 'inf', 'sfw', 'ecpc', 'tototf']]
        for idx in coords.index:
                text = coords.loc[idx,'obsnm']+ '<br>현재 수위 :' + str(coords.loc[idx,'swl']) + '<br>유입량 :' + str(coords.loc[idx,'inf'])+ '<br>저수량 :' + str(coords.loc[idx,'sfw']) + '<br>공용량 :' + str(coords.loc[idx,'ecpc']) + '<br>총 방류량 :' + str(coords.loc[idx,'tototf'])
                folium.Marker([coords.loc[idx, 'lat'], coords.loc[idx, 'lon']], icon = folium.Icon(color="purple"), tooltip = text).add_to(m)
        return m    

def flood():
    st.header("🌊홍수관련 실시간 정보")
    st.write("위치 정보를 선택하여 가까운 관측소 실시간 정보를 받아보세요🙏")
    
    st.markdown("###### 지도가 표시되지 않는다면 시도 선택을 다시 시도해주세요.")



    tab1, tab2, tab3 = st.tabs(["🌊실시간 수위 정보", '🏞️실시간 댐 정보', '🏞️실시간 보 정보'])
    with tab1:
        
        cd_nm = st.selectbox('시도 선택',['전국','강원도', '충청북도', '경상북도', '경기도', '서울특별시', '충청남도', '대구광역시', '경상남도',
                                            '전라북도', '부산광역시', '울산광역시', '대전광역시', '세종특별자치시', '전라남도', '광주광역시',
                                            '전남'])
        with st.spinner('정보 조회 중입니다. 잠시 기다려주세요.'):
            # 수위 데이터 조회
            data = flowsite()
            
            # 지역별 수위 데이터
            if cd_nm == "전국":
                data = data
            else :
                data = data[data['시도명'] == cd_nm]
            
            # 수위 데이터 시각화
            map = flow_map(data)
            st_folium(map, returned_objects=[])
            image = Image.open(os.path.join(filePath, 'using_data','수위.png'))
            st.markdown("###### 마커 색별 수위 정보")
            st.image(image, caption=None, width=None, use_column_width=None)
            st.write(f"현재 {(datetime.now()+ timedelta(hours = 9)).strftime('%Y-%m-%d %H:%M:%S')} 기준, 10분 단위로 최신 업데이트 된 정보입니다. 해당 페이지는 한강홍수통제소의 데이터를 사용합니다😊")


    with tab2:
        with st.spinner('정보 조회 중입니다. 잠시 기다려주세요.'):
            if st.button("전국 댐 정보보기 클릭"):
                dam_data = dam_data_make()
                m = dam_map(dam_data)
                st_folium(m , returned_objects=[])
                st.write(f"현재 {(datetime.now()+ timedelta(hours = 9)).strftime('%Y-%m-%d %H:%M:%S')} 기준, 1시간 단위로 최신 업데이트 된 정보입니다. 해당 페이지는 한강홍수통제소의 데이터를 사용합니다😊")
                
    with tab3:
        with st.spinner('정보 조회 중입니다. 잠시 기다려주세요.'):
            if st.button("전국 보 정보보기 클릭"):
                bo_data = bo_data_make()
                m = bo_map(bo_data)
                st_folium(m, returned_objects=[])
                st.write(f"현재 {(datetime.now()+ timedelta(hours = 9)).strftime('%Y-%m-%d %H:%M:%S')} 기준, 1시간 단위로 최신 업데이트 된 정보입니다. 해당 페이지는 한강홍수통제소의 데이터를 사용합니다😊")




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

def Shelter_map(data):
        m = folium.Map(
        location=[data['lat'].mean(), data['lon'].mean()],
        zoom_start= 7, width = '70%', height = '50%'
        )
        marker_cluster = MarkerCluster().add_to(m)
        for idx in data.index:
                text = data.loc[idx, 'shel_nm'] + '<br>상세주소 :' + data.loc[idx, 'address'] + '<br>수용 가능 인원수 :' + str(data.loc[idx, 'shel_av'])  + '<br>해변으로부터 거리 :' + str(data.loc[idx, 'lenth']) + 'M' + '<br>해발 높이 :' + str(data.loc[idx, 'height']) + '<br>내진적용여부 :' + data.loc[idx, 'seismic']
                folium.Marker([data.loc[idx, 'lat'], data.loc[idx, 'lon']], icon = folium.Icon(color="red"), tooltip = text).add_to(marker_cluster)
        return m
    
def earthbreak():
    st.header("🌊지진 해일 대피소 정보")
    st.write("지역을 선택하고 지도를 확대하면서, 가까운 지진해일 국내 대피소 정보를 받아보세요🙏")
    df = TsunamiShelter()
    sido_list = list(df['sido_name'].unique())
    sido_list.insert(0, '전국')
    cd_nm = st.sidebar.selectbox('시도 선택',sido_list)
    if cd_nm != '전국':
        df = df[df['sido_name'] == cd_nm]
    
    m = Shelter_map(df)
    st_folium(m, returned_objects=[])
    
    
def house():
    st.header("🏘️임시주거시설 정보")
    st.write("위치 정보를 선택하고 지도를 확대하면서, 가까운 임시주거시설 정보를 찾으세요🙏")
    data_path = os.path.join(filePath,'using_data','temporary_house.csv')
    df = pd.read_csv(data_path)


    cd_nm = st.selectbox('시도 선택',list(df['시도명'].unique()))
    sgg_nm = st.selectbox('시군구 선택',list(df[df['시도명'] == cd_nm]['시군구명'].unique()))
    df = df[(df['시도명'] == cd_nm) & (df['시군구명'] == sgg_nm)]





    # 지도 시각화
    mapping_data = df[['위도','경도','시설명', '상세주소', '시설면적', '주거능력', '지자체담당자연락처','관리부서']]

    m = folium.Map(
    location=[mapping_data['위도'].mean(), mapping_data['경도'].mean()],
    zoom_start= 10, width = '70%', height = '50%'
    )
    coords = mapping_data[['위도', '경도','시설명', '상세주소','시설면적', '주거능력','지자체담당자연락처', '관리부서']] 
    marker_cluster = MarkerCluster().add_to(m)
    for idx in coords.index:
        # popup 크기 설정
        text = coords.loc[idx,'시설명'] + '<br>상세주소 : ' + str(coords.loc[idx,'상세주소']) +'<br>시설면적 : ' + str(coords.loc[idx,'시설면적']) + '<br>주거능력 : ' + str(coords.loc[idx,'주거능력']) + '<br>관리부서 : ' + str(coords.loc[idx,'관리부서']) + '<br>지자체 담당자 연락처 : ' + str(coords.loc[idx,'지자체담당자연락처'])
        folium.Marker([coords.loc[idx,'위도'], coords.loc[idx,'경도']], icon = folium.Icon(color="purple"), tooltip = text).add_to(marker_cluster)
        
    st_folium(m, returned_objects=[])
    df = df.set_index('시설명')
    st.dataframe(data=df.drop(columns = ['시도명', '시군구명', '경도','위도']), use_container_width= True)
    
def mart():
    data_path = os.path.join(filePath,'using_data','구호물자정보.csv')

    st.header("💊긴급구호물자 구매업체")
    st.write("위치 정보를 선택하여 가까운 구매업체를 찾으세요🙏")
    df = pd.read_csv(data_path)

    cd_nm = st.selectbox('시도 선택',list(df['시도명'].unique()))
    sgg_nm = st.selectbox('시군구 선택',list(df[df['시도명'] == cd_nm]['시군구명'].unique()))
    df = df[(df['시도명'] == cd_nm) & (df['시군구명'] == sgg_nm)]
    df = df.set_index('업체명').drop(columns = ['시도명', '시군구명'])
    st.dataframe(data= df, use_container_width= True)


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


def hospital():
    data_path = os.path.join(filePath,'using_data','구호물자정보.csv')

    ####  title setting
    st.header("🚑응급의료기관 정보 실시간 조회")
    st.write("위치 정보를 선택하여 가까운 응급의료기관과 병실현황을 조회하세요!🙏")

    ####  select box data
    df = pd.read_csv(data_path)
    cd_nm = st.sidebar.selectbox('시도 선택',list(df['시도명'].unique()))
    sgg_nm = st.sidebar.selectbox('시군구 선택',list(df[df['시도명'] == cd_nm]['시군구명'].unique()))
    df = df[(df['시도명'] == cd_nm) & (df['시군구명'] == sgg_nm)]



    with st.spinner('정보 조회 중입니다. 잠시 기다려주세요.'):
        try:
            #### emergency hospital data 
            emergency_hospital_df = emergency_hospital(cd_nm, sgg_nm)

            #### make summary info
            emergency_hospital_df['응급실 가용현황'] = emergency_hospital_df['응급실 가용현황'].astype('int')
            sum = 0
            for i in emergency_hospital_df['응급실 가용현황']:
                if i > 0:
                    sum += i

            #### show summary info
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("지역 내 응급의료기관 수", str(len(emergency_hospital_df)) + '개')
            col2.metric('지역 내 응급실 가용병상', '총 ' + str(sum) + '개')
            emergency_hospital_df = emergency_hospital_df.set_index('기관명').drop(columns = '정보 업데이트 일시')
            st.dataframe(data=emergency_hospital_df, use_container_width= True)

        except Exception as E:
            st.write("😓죄송합니다. 해당 지역에 의료시설이 없습니다.")
            
def main():
    #make it look nice from the start
    st.set_page_config(page_title = "⛔위기 대응 프로젝트", layout='wide', initial_sidebar_state='collapsed',)

    with st.sidebar:
        st.markdown('**본 페이지는 홍수 위기 상황 발생 시<br>국민들의 즉각적인 상황 대처를 위해<br>제작 되었습니다**', unsafe_allow_html= True)
        st.markdown('개발자 깃허브 : https://github.com/sangwookWoo')
    #can apply customisation to almost all the properties of the card, including the progress bar
    theme_bad = {'bgcolor': '#FFF0F0','title_color': 'red','content_color': 'red','icon_color': 'red', 'icon': 'fa fa-times-circle'}
    theme_neutral = {'bgcolor': '#f9f9f9','title_color': 'orange','content_color': 'orange','icon_color': 'orange', 'icon': 'fa fa-question-circle'}
    theme_good = {'bgcolor': '#EFF8F7','title_color': 'green','content_color': 'green','icon_color': 'green', 'icon': 'fa fa-check-circle'}

    menu_data = [
        {'icon': "🌊", 'label':"홍수 실시간 정보"},
        {'icon':"☂️",'label':"실시간 단기 기상정보"},
        {'icon': "🧱",'label':"지진해일 대피소"},
        {'icon': "🏘️", 'label':"임시주거시설"},
        {'icon': "💊", 'label':"긴급구호물자 업체"},
        {'icon': "🚑", 'label':"응급의료기관 실시간 조회"},
    ]

    over_theme = {'txc_inactive': '#FFFFFF'}
    menu_id = hc.nav_bar(
        menu_definition = menu_data,
        override_theme = over_theme,
        home_name='HOME',
        # login_name='Logout',
        hide_streamlit_markers=True, #will show the st hamburger as well as the navbar now!
        sticky_nav=True, #at the top or not
        sticky_mode='pinned', #jumpy or not-jumpy, but sticky or pinned
    )
    
    if menu_id == 'HOME':
        home()
    elif menu_id == '홍수관련 실시간 정보':
        flood()
    elif menu_id == '실시간 초단기 기상정보':
        weather()
    elif menu_id == '지진해일 대피소 정보':
        earthbreak()
    elif menu_id == '임시주거시설 정보':
        house()
    elif menu_id == '긴급구호물자 구매업체':
        mart()
    elif menu_id == '응급의료기관 정보 실시간 조회':
        hospital()
    





    
if __name__ == "__main__":
    main()
    