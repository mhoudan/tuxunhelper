import requests
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs
import time
num = '12345667890'
#----------------------------------------------------------------------------------------
#request the  target http and get the text
def tuxun(pb,callback):
    url = 'https://b68g.daai.fun/maps/api/js/GeoPhotoService.GetMetadata'

    params = {
        'pb': pb,
        'callback': callback
    }

    headers = {
        'Host': 'b68g.daai.fun',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/139.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://tuxun.fun/',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    r = requests.get(url, headers=headers, params=params)
    print(r.status_code)
    data = r.text
    d = data.split('[')[:50]
    #print(data[:500])
    #print('\n')
    #print(d)
    return(d)
#------------------------------------------------------------------------------------------
#process the text and find the coordinates
def find(data:list):
    for i in range(len(data)):
        if '2025 Google' in data[i]:
            x = i
            break
    lat = data[x+5].split(']')[0].split(',')[-1]
    lng = data[x+5].split(']')[0].split(',')[-2]
    return lat,lng
#------------------------------------------------------------------------------------
#find parameters of the target http
def extract_pb_callback(url: str):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get('pb', [None])[0], params.get('callback', [None])[0]
#------------------------------------------------------------------------------------------
#request nominatim(free open map tool) with coord for exact info
def nominatim_coor_to_geocode(lat, lng):
    url = 'https://nominatim.openstreetmap.org/reverse'
    params = {
        'format': 'json',
        'lat': lat,
        'lon': lng,
        'zoom': 18,
        'addressdetails': 1,
        'accept-language': 'zh'
    }
    
    headers = {
        'User-Agent': 'tuxun/1.0'
    }
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None
#-------------------------------------------------------------------------------------------
#process the info from nominatim
def output(lat,lng):
    result = nominatim_coor_to_geocode(lat,lng)
    if result:
        print('address:', result.get('display_name'))
        print('country:', result.get('address', {}).get('country'))
        print('province:', result.get('address', {}).get('state'))
        print('city:', result.get('address', {}).get('city'))
        print('road:', result.get('address', {}).get('road'))
#----------------------------------------------------------------------------------
#main
def main():
    set_coords = set()
    map_page = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://tuxun.fun')
        #处理重复坐标
        def handle_repeat(lat, lng):
            nonlocal set_coords
            lat = float(lat)
            lng = float(lng)
            coord = (round(lat,3),round(lng,3))
            if not coord in set_coords:
                set_coords.add(coord)
                print(f"new coordinate:{coord}")
                output(lat, lng)
                return True
            return False
        #display the results on a new page
        def display(lat, lng):
            nonlocal map_page
            if map_page:
                map_page.close()
            map_page = browser.new_page() 
            url = 'https://nominatim.openstreetmap.org/ui/reverse.html?lat='+ lat + \
                  '&lon='+ lng + '&zoom=3'
            map_page.goto(url)
            time.sleep(0.1)
        #keep track on the network,get parameters,handle with the url
        def handle_request(request):
            if 'GeoPhotoService.GetMetadata' in request.url:
                pb, callback = extract_pb_callback(request.url)
                #print('\n新url:',request.url)
                #print('pb:', pb)
                #print('callback:',callback)
                lng, lat = find(tuxun(pb,callback))
                print(lat,lng)
                if handle_repeat(lat, lng):
                    display(lat,lng)
                #output(lat,lng)
        page.on('request', handle_request)

        print("每一轮都会输出最新URL") 
        page.wait_for_timeout(3000000)  # 等待

main()

