from pathlib import Path
import re
from playwright.sync_api import sync_playwright

# Synthetic-only browser proof: never signs in or calls production APIs.
def main():
    root=Path(__file__).resolve().parents[1]
    html=(root/'docs/corp/nhcso/index.html').read_text(encoding='utf-8')
    key=re.search(r"SESSION_KEY\s*=\s*'([^']+)'",html).group(1)
    requests=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            url=r.request.url
            if 'nhcso-workspace' in url:
                body=r.request.post_data_json;requests.append(body)
                if body['action']=='session_status': data={'email':'test@910cpr.com'}
                elif body['action']=='list_classes': data={'classes':[]}
                elif body['action']=='list_history':
                    offset=body['offset']
                    data={'history':[['2023-01-01','09:00',str(i),'Synthetic BLS','Synthetic room','Synthetic trainer'] for i in range(offset,min(offset+40,80))],'total':80,'next_offset':40 if offset==0 else None}
                else: raise AssertionError(body)
                r.fulfill(json=data);return
            if url.rstrip('/')=='https://www.910cpr.com/corp/nhcso':
                r.fulfill(body=html,content_type='text/html');return
            local=root/'docs'/url.split('www.910cpr.com/')[-1].split('?')[0]
            if local.is_file():
                r.fulfill(body=local.read_bytes(),content_type='text/javascript' if local.suffix=='.js' else 'text/css');return
            r.fulfill(body='',content_type='text/javascript')
        page.route('**/*',route)
        page.add_init_script('localStorage.setItem('+repr(key)+', JSON.stringify({token:"synthetic",email:"test@910cpr.com",expiresAt:"2099-01-01T00:00:00Z"}))')
        page.goto('https://www.910cpr.com/corp/nhcso/')
        page.wait_for_function('document.querySelectorAll(".class-card.history").length===40')
        page.locator('#moreHistory').click()
        page.wait_for_function('document.querySelectorAll(".class-card.history").length===80')
        metrics=page.locator('#classList').evaluate('(e)=>({height:e.clientHeight,scroll:e.scrollHeight,overflow:getComputedStyle(e).overflowY})')
        assert metrics['scroll']>metrics['height']>0,metrics
        last=page.locator('.class-card.history').last
        last.scroll_into_view_if_needed();assert last.is_visible()
        page.once('dialog',lambda d:d.accept());last.click()
        assert page.locator('#classNumber').inner_text()=='Class number assigned on save'
        assert page.locator('#moreHistory').is_hidden()
        assert [x['offset'] for x in requests if x['action']=='list_history']==[0,40]
        assert not errors,errors
        print({'result':'PASS','historical_cards':80,'pagination_offsets':[0,40],'scroll_metrics':metrics,'page_errors':errors,'writes':0})
        browser.close()

if __name__=='__main__': main()
