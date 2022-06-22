from selenium import webdriver
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import chromedriver_autoinstaller
import time, random, re

def connect_gspread(file_name, email=None):
    scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = 'omega-post-339414-4dcaa7da8bdb.json'
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)

    try:
        sheets = gc.open(file_name)
    except:
        sheets = gc.create(file_name)
    
    if email:
        sheets.share(value=email, perm_type='user', role='writer')

    return sheets

def write_gspread(output_sheet, books):
    colunms = [["_index", "_type", "_title", "_author", "search_sentence", "searched_sentence", "book_link", "_cover", "matched_text_page", "whole_text_page", "text_page_count", "downloaded"]]
    output_sheet.update("A1:L1", colunms)

    for index, book in enumerate(books):
        row = index + 2

        if book["empty"]:
            output_sheet.update_cell(row,1, book["index"])
            output_sheet.update_cell(row,2, book["type"])

        if not book["empty"]:
            output_sheet.update_cell(row,1, book["index"])
            output_sheet.update_cell(row,2, book["type"])
            output_sheet.update_cell(row,3, book["title"])
            output_sheet.update_cell(row,4, book["author"])
            output_sheet.update_cell(row,5, book["search_sentence"])
            output_sheet.update_cell(row,6, book["searched_sentence"])
            output_sheet.update_cell(row,7, book["book_link"])
            output_sheet.update_cell(row,8, book["cover_page_src"])
            output_sheet.update_cell(row,9, book["matched_page_src"])
            output_sheet.update_cell(row,10, " ".join(book["page_src_list"]))
            output_sheet.update_cell(row,11, len(book["page_src_list"]))
            output_sheet.update_cell(row,12, "no")
    
        index += 1

def get_book(browser, sentence):
    
    candidates, content_blocks = search_candidates(browser, sentence)

    if candidates:
        compared = compare(candidates)

        if compared:
            sentence, searched_sentence, _index = compared

            book_link = content_blocks[_index].find_element_by_tag_name("a")
            book_link.click()
            time.sleep(random.uniform(2,3))

            book = get_book_info(browser)
            book["search_sentence"] = sentence
            book["searched_sentence"] = searched_sentence
            book["book_link"] = browser.current_url
            book["page_src_list"] = get_book_page_src(browser)
            book["empty"] = False

            return book

    else:
        print("후보군 없음")
        return {}

def search_candidates(browser, sentence):
    
    # 검색 박스
    q_box = browser.find_element_by_xpath('//*[@id="oc-search-input"]')
    q_box.clear()
    q_box.send_keys(f'"{sentence}"')
    time.sleep(random.uniform(2,3))

    # 검색 버튼
    search_button = browser.find_element_by_xpath('//*[@id="oc-search-button"]/input')
    search_button.click()
    time.sleep(random.uniform(2,3))

    # 검색 결과
    content_blocks = browser.find_elements_by_class_name("Yr5TG")

    candidates = []
    for index, block in enumerate(content_blocks):

        try:
            # 미리보기 or 전체보기 가능한 결과물
            block.find_element_by_class_name("x9emld.FC2N5c")

            try:
                # 저자 이름 한글 -> 부적합
                author_text = block.find_element_by_class_name("N96wpd").text
                if author_text.upper() != author_text.lower():
                    
                    try:
                        searched_text = block.find_element_by_class_name("cmlJmd.ETWPw").text.split("\n")[-1]
                        compare_set = [sentence, searched_text, index]
                        candidates.append(compare_set)
                        print(f"{index + 1}번째 결과물: ", "possible")

                    except:
                        print(f"{index + 1}번째 결과물: ", "no searched text")
                        continue
                    
                else:
                    print(f"{index + 1}번째 결과물: ", "korean book")

            except:
                print(f"{index + 1}번째 결과물: ", "no author")
                continue

        except:
            print(f"{index + 1}번째 결과물: ", "no preivew")
            continue
    
    return candidates, content_blocks

def compare(candidates):

    for candidate in candidates:
        sentence, searched_sentence, index = candidate

        re_sentence = re.sub("“|”|’|'|—|―|–|-|,|\.| |\"", "", sentence).lower().strip()
        re_searched_sentence = re.sub("“|”|’|'|—|―|–|-|,|\.| |\"", "", searched_sentence).lower().strip()

        if re_sentence in re_searched_sentence:
            print(f"{index + 1}번째 결과에 찾는 문장이 있습니다.")
            return candidate

    print(f"{sentence}]를 발견할 수 없습니다.")
    return False

def get_book_info(browser):
    book_info = {}

    # 검색된 페이지 주소
    book_info["matched_page_src"] = browser.find_elements_by_class_name("pageImageDisplay")[0].find_element_by_tag_name("img").get_attribute("src")
    # 커버 페이지 주소
    book_info["cover_page_src"] = browser.find_element_by_id("summary-frontcover").get_attribute('src')

    # 제목 / 저자
    try:
        book_info["title"] = browser.find_element_by_class_name("gb-volume-title").text
    except:
        book_info["title"] = ""
    try:
        book_info["author"] = browser.find_element_by_class_name("addmd").text
    except:
        book_info["author"] = ""

    return book_info

def get_book_page_src(browser):
    # 커버 이미지 클릭 후 첫 페이지 이동 
    cover_img = browser.find_element_by_id("summary-frontcover")
    cover_img.click()
    time.sleep(random.uniform(2,3))

     # 다음 페이지 버튼
    i = 1
    next_button = browser.find_elements_by_class_name('jfk-button-img')[-2]
    page_src_list = []

    # pageImageDisplay에 있는 img source 리스트에 담기 (리스트에 있으면 담지 않는다.)
    while True:
        pages = browser.find_elements_by_class_name("pageImageDisplay")

        for page in pages:
            page_src = page.find_element_by_tag_name("img").get_attribute("src")

            if page_src and page_src not in page_src_list:     
                page_src_list.append(page_src)
        
        # pageImageDisplay 2개인 경우 종료 -> 마지막 페이지 (첫 페이지와 마지막 페이지만 2개 나머지 3개)
        if i >1 and len(browser.find_elements_by_class_name("pageImageDisplay")) == 2:
            break

        next_button.click()
        i += 1
        time.sleep(random.uniform(2,3))

    browser.back()
    return page_src_list

def main():
    sheets = connect_gspread(file_name="SSDA Scraping")
    
    input_sheet = sheets.worksheet("데이터 입력")
    num_list = input_sheet.col_values(1)[1:]
    type_list = input_sheet.col_values(2)[1:]
    f_sentence_list = input_sheet.col_values(3)[1:]
    s_sentence_list = input_sheet.col_values(4)[1:]

    year = input_sheet.col_values(6)[-1]
    grade = input_sheet.col_values(7)[-1]
    month = input_sheet.col_values(8)[-1]
    
    try:
        sheets.add_worksheet(title=f"{grade}학년{year}년{month}월", rows=100, cols=100)
    except:
        pass

    output_sheet = sheets.worksheet(f"{grade}학년{year}년{month}월")

    google_books_url = "https://books.google.co.kr/"
    
    chromedriver_autoinstaller.install()

    browser = webdriver.Chrome()
    browser.get(google_books_url)
    browser.implicitly_wait(10)

    books=[]
    for num, type, f_sentence, s_sentence in zip(num_list, type_list, f_sentence_list, s_sentence_list):

        if f_sentence:
            book = get_book(browser, sentence=f_sentence)

            if book:
                book["type"] = type
                book["index"] = f"H{grade}_{year}_{month}_{num}"
                books.append(book)
                browser.back()
                time.sleep(random.uniform(2,3))

            else:
                browser.back()
                time.sleep(random.uniform(2,3))

                book = get_book(browser, sentence=s_sentence)

                if book:
                    book["type"] = type
                    book["index"] = f"H{grade}_{year}_{month}_{num}"
                    books.append(book)
                    browser.back()
                    time.sleep(random.uniform(2,3))
                
                else:
                    browser.back()
                    empty_book = {"empty":True}
                    empty_book["type"] = type
                    empty_book["index"] = f"H{grade}_{year}_{month}_{num}"
                    books.append(empty_book)
                    time.sleep(random.uniform(2,3))

    write_gspread(output_sheet, books)

main()
