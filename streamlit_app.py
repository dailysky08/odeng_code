import streamlit as st
import hashlib
import sqlite3


# ===== 사용자 관련 DB 함수 =====
def create_user_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    conn.close()


def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    return user


# ===== 위키 페이지 관련 DB 함수 =====
def create_pages_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE,
            content TEXT,
            author TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_page(title, content, author):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO pages (title, content, author) VALUES (?, ?, ?)", (title, content, author))
        conn.commit()
    except sqlite3.IntegrityError:
        st.error("해당 제목의 페이지가 이미 존재합니다. 다른 제목을 사용하거나 기존 페이지를 편집하세요.")
    conn.close()


def update_page(title, content, author):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE pages SET content = ?, updated_at = CURRENT_TIMESTAMP, author = ? WHERE title = ?",
              (content, author, title))
    conn.commit()
    conn.close()


def get_all_pages():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT title, author, updated_at FROM pages ORDER BY updated_at DESC")
    pages = c.fetchall()
    conn.close()
    return pages


def get_page_by_title(title):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT title, content, author, created_at, updated_at FROM pages WHERE title = ?", (title,))
    page = c.fetchone()
    conn.close()
    return page


# ===== 메인 함수 =====
def main():
    st.set_page_config(page_title="Wiki System", layout="wide")
    st.title("Wiki System - 나무위키 스타일")

    # DB 테이블 생성
    create_user_table()
    create_pages_table()

    # 세션 상태 초기화
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
    if "menu_choice" not in st.session_state:
        st.session_state.menu_choice = "Login"
    if "wiki_mode" not in st.session_state:
        st.session_state.wiki_mode = "홈"  # 기본 위키 모드

    # 헤더: 로그인/회원가입 버튼
    col1, col2 = st.columns([8, 1])
    with col2:
        if not st.session_state.logged_in:
            if st.button("Login", key="login_btn_header"):
                st.session_state.menu_choice = "Login"
            if st.button("Sign Up", key="signup_btn_header"):
                st.session_state.menu_choice = "Sign Up"

    if st.session_state.logged_in:
        st.success(f"Logged in as {st.session_state.username}")
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.experimental_rerun()
    else:
        # 로그인/회원가입 폼 표시
        if st.session_state.menu_choice == "Login":
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", key="login_btn"):
                user = login_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login Successful")
                    st.experimental_rerun()
                else:
                    st.error("Invalid Username or Password")
        elif st.session_state.menu_choice == "Sign Up":
            st.subheader("Sign Up")
            new_user = st.text_input("New Username", key="signup_username")
            new_password = st.text_input("New Password", type="password", key="signup_password")
            if st.button("Sign Up", key="signup_btn"):
                add_user(new_user, new_password)
                st.success("Account created! Please log in.")
                st.experimental_rerun()

    # ===== 위키 사이드바 네비게이션 =====
    st.sidebar.title("Wiki Navigation")
    wiki_options = ["홈", "페이지 선택", "새 페이지 만들기"]
    # 편집 모드일 때는 사이드바에서 메뉴 선택이 덮어쓰지 않도록 함.
    if "edit_page" not in st.session_state:
        st.session_state.wiki_mode = st.sidebar.radio(
            "메뉴",
            wiki_options,
            index=wiki_options.index(st.session_state.wiki_mode) if st.session_state.wiki_mode in wiki_options else 0
        )

    # ===== 위키 메인 콘텐츠 =====
    if st.session_state.wiki_mode == "홈":
        st.subheader("Wiki 홈")
        st.write("나무위키 스타일 위키에 오신 것을 환영합니다!")
        st.markdown("최근 업데이트된 페이지:")
        pages = get_all_pages()
        if pages:
            for page in pages:
                title, author, updated_at = page
                st.markdown(f"**[{title}](?page={title})** - Last updated by {author} on {updated_at}")
        else:
            st.info("등록된 페이지가 없습니다.")

    elif st.session_state.wiki_mode == "페이지 선택":
        st.subheader("페이지 선택")
        pages = get_all_pages()
        if pages:
            page_titles = [page[0] for page in pages]
            selected_title = st.selectbox("페이지 제목 선택", page_titles)
            if selected_title:
                page = get_page_by_title(selected_title)
                if page:
                    title, content, author, created_at, updated_at = page
                    st.markdown(f"# {title}")
                    st.markdown(f"**작성자:** {author} | **생성일:** {created_at} | **마지막 수정:** {updated_at}")
                    st.write(content)
                    # 로그인한 경우 수정 버튼 제공
                    if st.session_state.logged_in:
                        if st.button("이 페이지 수정하기"):
                            st.session_state.edit_page = title
                            st.session_state.wiki_mode = "페이지 수정"
                            st.experimental_rerun()
        else:
            st.info("등록된 페이지가 없습니다.")

    elif st.session_state.wiki_mode == "새 페이지 만들기":
        st.subheader("새 페이지 만들기")
        if st.session_state.logged_in:
            new_title = st.text_input("페이지 제목", key="new_page_title")
            new_content = st.text_area("페이지 내용", key="new_page_content")
            if st.button("페이지 생성"):
                if new_title and new_content:
                    add_page(new_title, new_content, st.session_state.username)
                    st.success("페이지가 생성되었습니다!")
                    st.experimental_rerun()
                else:
                    st.error("제목과 내용을 모두 입력하세요.")
        else:
            st.error("새 페이지를 만들려면 로그인 해주세요.")

    elif st.session_state.wiki_mode == "페이지 수정":
        st.subheader("페이지 수정")
        # 'edit_page' 세션 변수에 수정할 페이지의 제목이 저장되어 있음
        if "edit_page" in st.session_state:
            title_to_edit = st.session_state.edit_page
            page = get_page_by_title(title_to_edit)
            if page:
                title, content, author, created_at, updated_at = page
                st.markdown(f"**페이지 제목:** {title}")
                updated_content = st.text_area("수정할 내용", value=content, key="edit_page_content")
                if st.button("수정 저장"):
                    if updated_content:
                        update_page(title, updated_content, st.session_state.username)
                        st.success("페이지가 수정되었습니다!")
                        # 수정 완료 후 페이지 선택 모드로 전환
                        st.session_state.wiki_mode = "페이지 선택"
                        del st.session_state.edit_page
                        st.experimental_rerun()
                    else:
                        st.error("내용을 입력해주세요.")
            else:
                st.error("수정할 페이지를 찾을 수 없습니다.")
        else:
            st.error("수정할 페이지가 선택되지 않았습니다.")


if __name__ == "__main__":
    main()
