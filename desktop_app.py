"""
한자 학습 데스크톱 애플리케이션
Flet 기반 전국한자능력검정시험 대비용 한자 학습 앱
"""
import flet as ft
import sqlite3
import random
import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import mm

# Database path
DATABASE = os.path.join(os.path.dirname(__file__), 'making_hanja.sqlite3')

# Register CJK font for PDF
pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
CJK_FONT = 'HYSMyeongJo-Medium'

# Grade order for sorting
GRADE_OPTIONS = [
    "전체", "8급", "7급Ⅱ", "7급", "6급Ⅱ", "6급",
    "5급Ⅱ", "5급", "4급Ⅱ", "4급", "3급Ⅱ", "3급",
    "2급", "1급", "특급Ⅱ", "특급"
]


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def main(page: ft.Page):
    """Main application entry point."""
    page.title = "한자 학습 - 전국한자능력검정시험 대비"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 1000
    page.window.height = 700
    page.padding = 0
    
    # State variables
    current_view = "home"
    selected_grade = ""
    hanja_list = []
    current_page_num = 1
    per_page = 20
    total_count = 0
    search_query = ""
    
    # Flashcard state
    flashcard_list = []
    flashcard_index = 0
    show_answer = False
    
    # Quiz state
    quiz_list = []
    quiz_index = 0
    quiz_score = 0
    quiz_options = []
    quiz_result = ""
    
    def load_hanja(grade="", query="", page_num=1):
        """Load hanja list from database."""
        nonlocal hanja_list, total_count, current_page_num
        current_page_num = page_num
        
        db = get_db()
        offset = (page_num - 1) * per_page
        
        conditions = []
        params = []
        
        if grade and grade != "전체":
            conditions.append("level = ?")
            params.append(grade)
        if query:
            conditions.append("(hanja LIKE ? OR main_sound LIKE ? OR meaning LIKE ?)")
            params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) as cnt FROM hanja WHERE {where_clause}"
        total_count = db.execute(count_query, params).fetchone()['cnt']
        
        # Get page data
        data_query = f"""
            SELECT id, hanja, main_sound, meaning, level, radical, strokes, total_strokes
            FROM hanja WHERE {where_clause}
            ORDER BY level_order, main_sound
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        cursor = db.execute(data_query, params)
        hanja_list = [dict(row) for row in cursor.fetchall()]
        db.close()
    
    def load_random_hanja(grade="", count=10):
        """Load random hanja for flashcards/quiz."""
        db = get_db()
        
        if grade and grade != "전체":
            cursor = db.execute("""
                SELECT id, hanja, main_sound, meaning, level
                FROM hanja WHERE level = ?
                ORDER BY RANDOM() LIMIT ?
            """, [grade, count])
        else:
            cursor = db.execute("""
                SELECT id, hanja, main_sound, meaning, level
                FROM hanja ORDER BY RANDOM() LIMIT ?
            """, [count])
        
        result = [dict(row) for row in cursor.fetchall()]
        db.close()
        return result
    
    def get_quiz_options(correct_meaning, count=4):
        """Get quiz options including the correct answer."""
        db = get_db()
        cursor = db.execute("""
            SELECT DISTINCT meaning FROM hanja
            WHERE meaning != ?
            ORDER BY RANDOM() LIMIT ?
        """, [correct_meaning, count - 1])
        options = [row['meaning'] for row in cursor.fetchall()]
        db.close()
        options.append(correct_meaning)
        random.shuffle(options)
        return options
    
    def generate_pdf(grade="", count=10, repeat=10):
        """Generate practice PDF."""
        hanja_data = load_random_hanja(grade, count)
        
        if not hanja_data:
            return None
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Title
        c.setFont(CJK_FONT, 16)
        today = datetime.now().strftime("%Y년 %m월 %d일")
        grade_text = f" ({grade})" if grade and grade != "전체" else ""
        c.drawCentredString(width / 2, height - 30 * mm, f"일일 한자 쓰기 연습{grade_text}")
        c.setFont(CJK_FONT, 10)
        c.drawCentredString(width / 2, height - 38 * mm, today)
        
        # Settings for grid
        start_y = height - 55 * mm
        left_margin = 15 * mm
        cell_size = 18 * mm
        info_width = 55 * mm
        
        for idx, hanja in enumerate(hanja_data):
            row_y = start_y - (idx * (cell_size + 5 * mm))
            
            if row_y < 25 * mm:
                c.showPage()
                start_y = height - 25 * mm
                row_y = start_y - ((idx % 10) * (cell_size + 5 * mm))
            
            c.setFont(CJK_FONT, 8)
            c.drawString(left_margin, row_y + 12 * mm, f"[{hanja['level']}]")
            
            c.setFont(CJK_FONT, 28)
            c.drawString(left_margin, row_y - 2 * mm, hanja['hanja'])
            
            c.setFont(CJK_FONT, 9)
            c.drawString(left_margin + 22 * mm, row_y + 8 * mm, f"{hanja['main_sound']}")
            
            meaning_text = hanja['meaning'][:20] + "..." if len(hanja['meaning']) > 20 else hanja['meaning']
            c.drawString(left_margin + 22 * mm, row_y, meaning_text)
            
            grid_start_x = left_margin + info_width
            for i in range(repeat):
                box_x = grid_start_x + (i * cell_size)
                if box_x + cell_size > width - 10 * mm:
                    break
                c.setStrokeColorRGB(0.7, 0.7, 0.7)
                c.setLineWidth(0.5)
                c.rect(box_x, row_y - 3 * mm, cell_size - 2 * mm, cell_size - 2 * mm)
                c.setStrokeColorRGB(0.85, 0.85, 0.85)
                c.setDash(2, 2)
                center_x = box_x + (cell_size - 2 * mm) / 2
                center_y = row_y - 3 * mm + (cell_size - 2 * mm) / 2
                c.line(box_x, center_y, box_x + cell_size - 2 * mm, center_y)
                c.line(center_x, row_y - 3 * mm, center_x, row_y - 3 * mm + cell_size - 2 * mm)
                c.setDash()
        
        c.setFont(CJK_FONT, 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width / 2, 10 * mm, "한자 학습 - 전국한자능력검정시험 대비")
        
        c.save()
        buffer.seek(0)
        return buffer.getvalue()
    
    # UI Components
    def create_navbar():
        """Create navigation bar."""
        def nav_click(e, view):
            nonlocal current_view
            current_view = view
            update_content()
        
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Text("漢", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("한자 학습", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=10),
                ft.Row([
                    ft.TextButton("홈", on_click=lambda e: nav_click(e, "home"),
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                    ft.TextButton("한자 목록", on_click=lambda e: nav_click(e, "list"),
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                    ft.TextButton("플래시카드", on_click=lambda e: nav_click(e, "flashcard"),
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                    ft.TextButton("퀴즈", on_click=lambda e: nav_click(e, "quiz"),
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                    ft.TextButton("쓰기 연습", on_click=lambda e: nav_click(e, "practice"),
                                  style=ft.ButtonStyle(color=ft.Colors.WHITE)),
                ], spacing=5),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=10),
            gradient=ft.LinearGradient(
                begin=ft.alignment.center_left,
                end=ft.alignment.center_right,
                colors=["#667eea", "#764ba2"],
            ),
        )
    
    def create_home_view():
        """Create home view."""
        return ft.Container(
            content=ft.Column([
                ft.Text("전국한자능력검정시험 대비", size=32, weight=ft.FontWeight.BOLD, 
                        color="#667eea", text_align=ft.TextAlign.CENTER),
                ft.Text("한자 학습 데스크톱 앱", size=18, color="#666",
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=30),
                ft.Row([
                    create_feature_card("📚", "한자 목록", "5,978개 한자 검색 및 조회", "list"),
                    create_feature_card("🎴", "플래시카드", "카드로 암기 학습", "flashcard"),
                    create_feature_card("❓", "퀴즈", "4지선다 퀴즈", "quiz"),
                    create_feature_card("✏️", "쓰기 연습", "PDF 다운로드", "practice"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=50,
        )
    
    def create_feature_card(icon, title, desc, view):
        """Create a feature card."""
        def on_click(e):
            nonlocal current_view
            current_view = view
            update_content()
        
        return ft.Container(
            content=ft.Column([
                ft.Text(icon, size=40),
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(desc, size=12, color="#666"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=20,
            bgcolor=ft.Colors.WHITE,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color="#00000020"),
            on_click=on_click,
            width=180,
            height=150,
        )
    
    def create_grade_dropdown(on_change_callback):
        """Create grade dropdown."""
        return ft.Dropdown(
            label="급수 선택",
            options=[ft.dropdown.Option(g) for g in GRADE_OPTIONS],
            value="전체",
            width=200,
            on_change=on_change_callback,
        )
    
    def create_list_view():
        """Create hanja list view."""
        nonlocal selected_grade, search_query
        
        def on_grade_change(e):
            nonlocal selected_grade
            selected_grade = e.control.value if e.control.value != "전체" else ""
            load_hanja(selected_grade, search_query, 1)
            update_content()
        
        def on_search(e):
            nonlocal search_query
            search_query = e.control.value
            load_hanja(selected_grade, search_query, 1)
            update_content()
        
        def on_prev_page(e):
            if current_page_num > 1:
                load_hanja(selected_grade, search_query, current_page_num - 1)
                update_content()
        
        def on_next_page(e):
            total_pages = (total_count + per_page - 1) // per_page
            if current_page_num < total_pages:
                load_hanja(selected_grade, search_query, current_page_num + 1)
                update_content()
        
        load_hanja(selected_grade, search_query, current_page_num)
        total_pages = max(1, (total_count + per_page - 1) // per_page)
        
        hanja_cards = []
        for h in hanja_list:
            card = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(h['hanja'], size=36, weight=ft.FontWeight.BOLD, color="#667eea"),
                        ft.Column([
                            ft.Text(h['main_sound'], size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(h['meaning'][:30], size=12, color="#666"),
                        ], spacing=2),
                    ], spacing=15),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(h['level'], size=10, color=ft.Colors.WHITE),
                            bgcolor="#667eea",
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=10,
                        ),
                        ft.Text(f"부수: {h['radical']} | 획수: {h['total_strokes']}", size=10, color="#999"),
                    ], spacing=10),
                ], spacing=8),
                padding=15,
                bgcolor=ft.Colors.WHITE,
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=5, color="#00000010"),
            )
            hanja_cards.append(card)
        
        return ft.Container(
            content=ft.Column([
                ft.Text("한자 목록", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([
                    create_grade_dropdown(on_grade_change),
                    ft.TextField(label="검색", width=200, on_submit=on_search),
                    ft.Text(f"총 {total_count}개", color="#666"),
                ], spacing=20),
                ft.Container(
                    content=ft.Column(hanja_cards, spacing=10, scroll=ft.ScrollMode.AUTO),
                    height=400,
                ),
                ft.Row([
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_prev_page,
                                  disabled=current_page_num <= 1),
                    ft.Text(f"{current_page_num} / {total_pages} 페이지"),
                    ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=on_next_page,
                                  disabled=current_page_num >= total_pages),
                ], alignment=ft.MainAxisAlignment.CENTER),
            ], spacing=20),
            padding=30,
        )
    
    def create_flashcard_view():
        """Create flashcard view."""
        nonlocal flashcard_list, flashcard_index, show_answer, selected_grade
        
        def on_grade_change(e):
            nonlocal selected_grade
            selected_grade = e.control.value if e.control.value != "전체" else ""
        
        def start_flashcards(e):
            nonlocal flashcard_list, flashcard_index, show_answer
            flashcard_list = load_random_hanja(selected_grade, 20)
            flashcard_index = 0
            show_answer = False
            update_content()
        
        def toggle_answer(e):
            nonlocal show_answer
            show_answer = not show_answer
            update_content()
        
        def next_card(e):
            nonlocal flashcard_index, show_answer
            if flashcard_index < len(flashcard_list) - 1:
                flashcard_index += 1
                show_answer = False
                update_content()
        
        def prev_card(e):
            nonlocal flashcard_index, show_answer
            if flashcard_index > 0:
                flashcard_index -= 1
                show_answer = False
                update_content()
        
        content = [
            ft.Text("플래시카드", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                create_grade_dropdown(on_grade_change),
                ft.ElevatedButton("시작", on_click=start_flashcards, bgcolor="#667eea", color=ft.Colors.WHITE),
            ], spacing=20),
        ]
        
        if flashcard_list:
            current = flashcard_list[flashcard_index]
            card_content = [
                ft.Text(f"{flashcard_index + 1} / {len(flashcard_list)}", color="#666"),
                ft.Text(current['hanja'], size=80, weight=ft.FontWeight.BOLD, color="#667eea"),
            ]
            
            if show_answer:
                card_content.extend([
                    ft.Text(current['main_sound'], size=28),
                    ft.Text(current['meaning'], size=16, color="#666"),
                    ft.Container(
                        content=ft.Text(current['level'], size=12, color=ft.Colors.WHITE),
                        bgcolor="#667eea",
                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                        border_radius=15,
                    ),
                ])
            else:
                card_content.append(ft.Text("클릭하여 정답 보기", color="#999"))
            
            card = ft.Container(
                content=ft.Column(card_content, 
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                                  spacing=10),
                padding=40,
                bgcolor=ft.Colors.WHITE,
                border_radius=20,
                shadow=ft.BoxShadow(blur_radius=15, color="#00000020"),
                on_click=toggle_answer,
                width=400,
                height=350,
            )
            
            content.append(ft.Container(content=card, alignment=ft.alignment.center))
            content.append(ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=prev_card, 
                              disabled=flashcard_index <= 0, icon_size=30),
                ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=next_card,
                              disabled=flashcard_index >= len(flashcard_list) - 1, icon_size=30),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=50))
        else:
            content.append(ft.Text("시작 버튼을 클릭하세요", color="#666"))
        
        return ft.Container(
            content=ft.Column(content, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=30,
        )
    
    def create_quiz_view():
        """Create quiz view."""
        nonlocal quiz_list, quiz_index, quiz_score, quiz_options, quiz_result, selected_grade
        
        def on_grade_change(e):
            nonlocal selected_grade
            selected_grade = e.control.value if e.control.value != "전체" else ""
        
        def start_quiz(e):
            nonlocal quiz_list, quiz_index, quiz_score, quiz_options, quiz_result
            quiz_list = load_random_hanja(selected_grade, 10)
            quiz_index = 0
            quiz_score = 0
            quiz_result = ""
            if quiz_list:
                quiz_options = get_quiz_options(quiz_list[0]['meaning'])
            update_content()
        
        def check_answer(answer):
            nonlocal quiz_result, quiz_score
            correct = quiz_list[quiz_index]['meaning']
            if answer == correct:
                quiz_result = "정답입니다! 🎉"
                quiz_score += 1
            else:
                quiz_result = f"오답입니다. 정답: {correct}"
            update_content()
        
        def next_question(e):
            nonlocal quiz_index, quiz_result, quiz_options
            quiz_index += 1
            quiz_result = ""
            if quiz_index < len(quiz_list):
                quiz_options = get_quiz_options(quiz_list[quiz_index]['meaning'])
            update_content()
        
        content = [
            ft.Text("한자 퀴즈", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([
                create_grade_dropdown(on_grade_change),
                ft.ElevatedButton("시작", on_click=start_quiz, bgcolor="#667eea", color=ft.Colors.WHITE),
            ], spacing=20),
        ]
        
        if quiz_list and quiz_index < len(quiz_list):
            current = quiz_list[quiz_index]
            
            question_card = ft.Container(
                content=ft.Column([
                    ft.Text(f"문제 {quiz_index + 1} / {len(quiz_list)}", color="#666"),
                    ft.Text(f"점수: {quiz_score}", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(current['hanja'], size=60, weight=ft.FontWeight.BOLD, color="#667eea"),
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15,
                    ),
                    ft.Text("이 한자의 뜻은?", size=16),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            )
            content.append(question_card)
            
            if not quiz_result:
                option_buttons = [
                    ft.ElevatedButton(
                        opt[:30] + "..." if len(opt) > 30 else opt,
                        on_click=lambda e, o=opt: check_answer(o),
                        width=350,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ) for opt in quiz_options
                ]
                content.append(ft.Column(option_buttons, spacing=10, 
                                         horizontal_alignment=ft.CrossAxisAlignment.CENTER))
            else:
                result_color = ft.Colors.GREEN if "정답" in quiz_result else ft.Colors.RED
                content.append(ft.Text(quiz_result, size=18, weight=ft.FontWeight.BOLD, color=result_color))
                content.append(ft.ElevatedButton("다음 문제", on_click=next_question, 
                                                  bgcolor="#667eea", color=ft.Colors.WHITE))
        
        elif quiz_list and quiz_index >= len(quiz_list):
            content.append(ft.Container(
                content=ft.Column([
                    ft.Text("퀴즈 완료!", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text(f"최종 점수: {quiz_score} / {len(quiz_list)}", size=20),
                    ft.ElevatedButton("다시 시작", on_click=start_quiz, bgcolor="#667eea", color=ft.Colors.WHITE),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
            ))
        else:
            content.append(ft.Text("시작 버튼을 클릭하세요", color="#666"))
        
        return ft.Container(
            content=ft.Column(content, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=30,
        )
    
    def create_practice_view():
        """Create writing practice PDF download view."""
        nonlocal selected_grade
        
        def on_grade_change(e):
            nonlocal selected_grade
            selected_grade = e.control.value if e.control.value != "전체" else ""
        
        def download_pdf(e):
            pdf_data = generate_pdf(selected_grade, 10, 10)
            if pdf_data:
                filename = f"hanja_practice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                filepath = os.path.join(os.path.expanduser("~/Downloads"), filename)
                with open(filepath, 'wb') as f:
                    f.write(pdf_data)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"PDF가 다운로드 폴더에 저장되었습니다: {filename}"),
                    bgcolor=ft.Colors.GREEN,
                )
                page.snack_bar.open = True
                page.update()
        
        return ft.Container(
            content=ft.Column([
                ft.Text("일일 한자 쓰기 연습", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("랜덤으로 선택된 한자를 10번씩 쓰기 연습할 수 있는 PDF를 다운로드하세요.", 
                        color="#666"),
                ft.Container(height=20),
                create_grade_dropdown(on_grade_change),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.DESCRIPTION, size=60, color="#667eea"),
                        ft.Text("A4 크기 PDF", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text("10개 한자 × 10번 쓰기", color="#666"),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    padding=30,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    shadow=ft.BoxShadow(blur_radius=10, color="#00000020"),
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "PDF 다운로드",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=download_pdf,
                    bgcolor="#667eea",
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(padding=20),
                ),
                ft.Text("* 매번 다른 랜덤 한자가 선택됩니다", color="#999", size=12),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=50,
        )
    
    def update_content():
        """Update main content based on current view."""
        if current_view == "home":
            content_area.content = create_home_view()
        elif current_view == "list":
            content_area.content = create_list_view()
        elif current_view == "flashcard":
            content_area.content = create_flashcard_view()
        elif current_view == "quiz":
            content_area.content = create_quiz_view()
        elif current_view == "practice":
            content_area.content = create_practice_view()
        page.update()
    
    # Main layout
    content_area = ft.Container(
        content=create_home_view(),
        expand=True,
        bgcolor="#f8f9fa",
    )
    
    page.add(
        ft.Column([
            create_navbar(),
            content_area,
        ], spacing=0, expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
