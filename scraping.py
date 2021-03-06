from selenium import webdriver
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import chromedriver_autoinstaller
import time, random, re, sys, os
import urllib.request as req

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def connect_gspread(file_name, email=None):
    scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
    ]
    json_file_name = resource_path('./lxper.json')
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file_name, scope)
    gc = gspread.authorize(credentials)

    try:
        sheets = gc.open(file_name)
    except:
        sheets = gc.create(file_name)
    
    if email:
        sheets.share(value=email, perm_type='user', role='writer')

    return sheets

def write_gspread(output_sheet, num, book):
    colunms = [["_index", "_type", "_title", "_author", "search_sentence", "searched_sentence", "book_link", "_cover", "matched_text_page", "whole_text_page", "text_page_count", "downloaded"]]
    output_sheet.update("A1:L1", colunms)

    row = int(num) - 16
    if num == 43:
        row = num - 17

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

            try:
                book["page_src_list"] = get_book_page_src(browser)
            except:
                book["page_src_list"] = ""

            book["empty"] = False

            return book

    else:
        print("????????? ??????")
        return {}

def search_candidates(browser, sentence):
    
    # ?????? ??????
    q_box = browser.find_element_by_xpath('//*[@id="oc-search-input"]')
    q_box.clear()
    q_box.send_keys(f'"{sentence}"')
    time.sleep(random.uniform(2,3))

    # ?????? ??????
    search_button = browser.find_element_by_xpath('//*[@id="oc-search-button"]/input')
    search_button.click()
    time.sleep(random.uniform(2,3))

    # ?????? ??????
    content_blocks = browser.find_elements_by_class_name("Yr5TG")

    candidates = []
    for index, block in enumerate(content_blocks):

        try:
            # ???????????? or ???????????? ????????? ?????????
            block.find_element_by_class_name("x9emld.FC2N5c")

            try:
                # ?????? ?????? ?????? -> ?????????
                author_text = block.find_element_by_class_name("N96wpd").text
                if author_text.upper() != author_text.lower():
                    
                    try:
                        searched_text = block.find_element_by_class_name("cmlJmd.ETWPw").text.split("\n")[-1]
                        compare_set = [sentence, searched_text, index]
                        candidates.append(compare_set)
                        print(f"{index + 1}?????? ?????????: ", "possible")

                    except:
                        print(f"{index + 1}?????? ?????????: ", "no searched text")
                        continue
                    
                else:
                    print(f"{index + 1}?????? ?????????: ", "korean book")

            except:
                print(f"{index + 1}?????? ?????????: ", "no author")
                continue

        except:
            print(f"{index + 1}?????? ?????????: ", "no preivew")
            continue
    
    return candidates, content_blocks

def compare(candidates):

    for candidate in candidates:
        sentence, searched_sentence, index = candidate

        re_sentence = re.sub("???|???|???|'|???|???|???|-|,|\.| |\"", "", sentence).lower().strip()
        re_searched_sentence = re.sub("???|???|???|'|???|???|???|-|,|\.| |\"", "", searched_sentence).lower().strip()

        if re_sentence in re_searched_sentence:
            print(f"{index + 1}?????? ????????? ?????? ????????? ????????????.")
            return candidate

    print(f"{sentence}]??? ????????? ??? ????????????.")
    return False

def get_book_info(browser):
    book_info = {}

    # ????????? ????????? ??????
    book_info["matched_page_src"] = browser.find_elements_by_class_name("pageImageDisplay")[0].find_element_by_tag_name("img").get_attribute("src")
    # ?????? ????????? ??????
    book_info["cover_page_src"] = browser.find_element_by_id("summary-frontcover").get_attribute('src')

    # ?????? / ??????
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
    # ?????? ????????? ?????? ??? ??? ????????? ?????? 
    cover_img = browser.find_element_by_id("summary-frontcover")
    cover_img.click()
    time.sleep(random.uniform(2,3))

     # ?????? ????????? ??????
    i = 1
    next_button = browser.find_elements_by_class_name('jfk-button-img')[-2]
    page_src_list = []

    # pageImageDisplay??? ?????? img source ???????????? ?????? (???????????? ????????? ?????? ?????????.)
    while True:
        pages = browser.find_elements_by_class_name("pageImageDisplay")

        for page in pages:

            page_src = page.find_element_by_tag_name("img").get_attribute("src")

            if page_src and page_src not in page_src_list:     
                page_src_list.append(page_src)
        
        # pageImageDisplay 2?????? ?????? ?????? -> ????????? ????????? (??? ???????????? ????????? ???????????? 2??? ????????? 3???)
        if i >1 and len(browser.find_elements_by_class_name("pageImageDisplay")) == 2:
            break

        next_button.click()
        i += 1
        time.sleep(random.uniform(2,3))

    browser.back()
    return page_src_list

def image_download(output_sheet):
    WORKING_DIR = r"\\192.168.219.102\LXPER-Share2\?????????????????????"
    os.chdir(WORKING_DIR)

    index_col = output_sheet.find("_index").col
    index_list = output_sheet.col_values(index_col)[1:]
    
    cover_col = output_sheet.find("_cover").col
    cover_list = output_sheet.col_values(cover_col)[1:]

    matched_page_col = output_sheet.find("matched_text_page").col
    matched_page_list = output_sheet.col_values(matched_page_col)[1:]
    
    whole_page_col = output_sheet.find("whole_text_page").col
    whole_page_list = output_sheet.col_values(whole_page_col)[1:]
    
    for index, cover_src, matched_src, whole_srcs in zip(index_list, cover_list, matched_page_list, whole_page_list):

        if whole_srcs:
            grade = index.split("_")[0][-1]
            year = index.split("_")[1]
            month = index.split("_")[2]
            number = index.split("_")[3]
            save_path = f"./google_books/{grade}??????/{year}??????/{month}???/{number}"

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            req.urlretrieve(cover_src, f"{save_path}\{index}_cover")
            req.urlretrieve(matched_src, f"{save_path}\{index}_matched")
            time.sleep(random.uniform(0,1))

            splited_whole_src = whole_srcs.split(" ")
            for counter, page_src in enumerate(splited_whole_src):
                
                if counter < 9:
                    tmp = f'00{counter + 1}'

                elif counter < 99:
                    tmp = f'0{counter + 1}'

                try:
                    req.urlretrieve(page_src, f"{save_path}\{index}_{tmp}")
                except:
                    print("error")
                
def main():
    sheets = connect_gspread(file_name="SSDA Scraping Tool")
    
    input_sheet = sheets.worksheet("????????? ??????")
    num_list = input_sheet.col_values(1)[1:]
    type_list = input_sheet.col_values(2)[1:]
    f_sentence_list = input_sheet.col_values(3)[1:]
    s_sentence_list = input_sheet.col_values(4)[1:]

    year = input_sheet.col_values(6)[-1]
    grade = input_sheet.col_values(7)[-1]
    month = input_sheet.col_values(8)[-1]
    
    try:
        sheets.add_worksheet(title=f"{grade}??????{year}???{month}???", rows=100, cols=100)
    except:
        pass

    output_sheet = sheets.worksheet(f"{grade}??????{year}???{month}???")

    google_books_url = "https://books.google.co.kr/"
    
    chromedriver_autoinstaller.install()

    browser = webdriver.Chrome()
    browser.get(google_books_url)
    browser.implicitly_wait(10)

    for num, type, f_sentence, s_sentence in zip(num_list, type_list, f_sentence_list, s_sentence_list):

        if f_sentence:
            book = get_book(browser, sentence=f_sentence)

            if book:
                book["type"] = type
                book["index"] = f"H{grade}_{year}_{month}_{num}"
                write_gspread(output_sheet, num, book)
                browser.back()
                time.sleep(random.uniform(2,3))

            else:
                browser.back()
                time.sleep(random.uniform(2,3))

                book = get_book(browser, sentence=s_sentence)

                if book:
                    book["type"] = type
                    book["index"] = f"H{grade}_{year}_{month}_{num}"
                    write_gspread(output_sheet, num, book)
                    browser.back()
                    time.sleep(random.uniform(2,3))
                
                else:
                    browser.back()
                    empty_book = {"empty":True}
                    empty_book["type"] = type
                    empty_book["index"] = f"H{grade}_{year}_{month}_{num}"
                    write_gspread(output_sheet, num, empty_book)
                    time.sleep(random.uniform(2,3))

    browser.quit()
    # image_download(output_sheet)

main()
