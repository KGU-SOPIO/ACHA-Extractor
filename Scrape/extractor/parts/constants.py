KUTIS_LOGIN_URL = "https://kutis.kyonggi.ac.kr/webkutis/view/hs/wslogin/loginCheck.jsp"
KUTIS_LOGIN_PAGE_URL = "https://kutis.kyonggi.ac.kr/webkutis/view/indexWeb.jsp"
KUTIS_MAIN_PAGE_URL = "https://kutis.kyonggi.ac.kr/webkutis/view/main/mypage.jsp?flag=2"
KUTIS_TIMETABLE_PAGE_URL = "https://kutis.kyonggi.ac.kr/webkutis/view/hs/wssu3/wssu330s.jsp?m_menu=wsco1s05&s_menu=wssu330s"

LMS_LOGIN_URL = "https://lms.kyonggi.ac.kr/login/index.php"
LMS_LOGIN_SUCCESS_URL = "https://lms.kyonggi.ac.kr/login/index.php?testsession="
LMS_LOGIN_FAILURE_URL = "https://lms.kyonggi.ac.kr/login.php?errorcode=3"

LMS_MAIN_PAGE_URL = "https://lms.kyonggi.ac.kr/"
LMS_USER_PAGE_URL = "https://lms.kyonggi.ac.kr/user/user_edit.php"
LMS_PAST_COURSE_PAGE_URL = (
    "https://lms.kyonggi.ac.kr/local/ubion/user/?year={}&semester={}"
)
LMS_COURSE_PAGE_URL = "https://lms.kyonggi.ac.kr/course/view.php?id={}"
LMS_ATTENDANCE_PAGE_URL = (
    "https://lms.kyonggi.ac.kr/report/ubcompletion/user_progress_a.php?id={}"
)
LMS_BOARD_PAGE_URL = "https://lms.kyonggi.ac.kr/mod/ubboard/view.php?id={}"
LMS_ASSIGNMENT_PAGE_URL = "https://lms.kyonggi.ac.kr/mod/assign/view.php?id={}"

LMS_ACTIVITY_TYPES = {
    "xncommons": "lecture",
    "assign": "assignment",
    "url": "url",
    "ubfile": "file",
}
