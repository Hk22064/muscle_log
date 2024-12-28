#gui.py
import tkinter as tk
import sqlite3

from tkinter import messagebox
from db_utils import get_progress_data
from db_utils import initialize_database
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib import font_manager
import threading

def show_progress(exercise_id):
    """
    種目IDに基づいて進捗をグラフで表示し、トレーニング詳細を表示する
    """
    data = get_progress_data(exercise_id)

    if data:
        dates, weights, reps, sets = zip(*data)

        # トレーニング詳細ウィンドウを表示（グラフと並行して表示）
        show_training_details(exercise_id, dates, weights, reps, sets)

        # グラフ表示を別スレッドで実行
        threading.Thread(target=display_graph, args=(dates, weights, reps, sets)).start()
    else:
        messagebox.showinfo("情報", "進捗データがありません！")

def display_graph(dates, weights, reps, sets):
    """
    別スレッドでグラフを表示
    """
    # 日本語フォントの設定（Windows環境での例）
    font_path = "C:/Windows/Fonts/msgothic.ttc"  # MSゴシック
    prop = font_manager.FontProperties(fname=font_path)

    # グラフ表示
    plt.figure(figsize=(8, 5))
    plt.plot(dates, weights, marker="o", label="重量推移", color="blue")
    plt.title("トレーニング進捗", fontsize=14, fontproperties=prop)
    plt.xlabel("日付", fontsize=12, fontproperties=prop)
    plt.ylabel("重量 (kg)", fontsize=12, fontproperties=prop)
    plt.xticks(rotation=45, fontproperties=prop)
    plt.legend(prop=prop)
    plt.tight_layout()
    plt.show()

def show_training_details(exercise_id, dates, weights, reps, sets):
    """
    トレーニングの詳細（日付とセット数）を表示するウィンドウ
    """
    window = tk.Toplevel()
    window.title("トレーニング詳細")

    # 重複した日付を取り除くため、setでユニークな日付を取得
    unique_dates = sorted(set(dates))

    def show_details_for_date(date):
        """選択した日付の詳細を表示"""
        details_window = tk.Toplevel()
        details_window.title(f"{date} の詳細")

        # 選択した日付のデータのみをフィルタリング
        for i in range(len(dates)):
            if dates[i] == date:
                frame = tk.Frame(details_window)
                frame.pack(pady=5)
                tk.Label(frame, text=f"セット: {sets[i]} | 重量: {weights[i]}kg | 回数: {reps[i]}回").pack()

    # ユニークな日付ごとに表示し、選択できるようにする
    for date in unique_dates:
        frame = tk.Frame(window)
        frame.pack(pady=5)

        tk.Label(frame, text=f"日付: {date} | セット数: {len(sets)}").pack(side="left")

        # 日付をクリックしたら、その日の詳細を表示
        tk.Button(frame, text="詳細", command=lambda date=date: show_details_for_date(date)).pack(side="right")

    tk.Button(window, text="閉じる", command=window.destroy).pack(pady=10)

def add_exercise():
    """
    種目を追加するウィンドウ
    """
    def save_exercise():
        name = entry_name.get()
        description = entry_desc.get()
        category = selected_category.get()

        if name and category:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Exercise (name, description, category) VALUES (?, ?, ?)", 
                               (name, description, category))
                conn.commit()
                conn.close()
                messagebox.showinfo("成功", "種目を追加しました！")
                window.destroy()
            except Exception as e:
                messagebox.showerror("エラー", f"データ保存に失敗しました: {e}")
        else:
            messagebox.showerror("エラー", "種目名とカテゴリーを選択してください！")

    window = tk.Toplevel()
    window.title("種目追加")

    tk.Label(window, text="種目名:").pack()
    entry_name = tk.Entry(window)
    entry_name.pack()

    tk.Label(window, text="説明:").pack()
    entry_desc = tk.Entry(window)
    entry_desc.pack()

    # カテゴリー選択のラジオボタン
    tk.Label(window, text="カテゴリー:").pack()
    selected_category = tk.StringVar()
    selected_category.set("胸")  # デフォルトのカテゴリー

    categories = ["胸", "背中", "足", "腕", "肩"]
    for category in categories:
        tk.Radiobutton(window, text=category, value=category, variable=selected_category).pack()

    tk.Button(window, text="保存", command=save_exercise).pack()
    
def show_exercise_list():
    """
    登録済みの種目一覧を表示するウィンドウ
    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description FROM Exercise")
    exercises = cursor.fetchall()

    window = tk.Toplevel()
    window.title("種目一覧")

    if exercises:
        for exercise in exercises:
            frame = tk.Frame(window)
            frame.pack(pady=5)

            # 各種目の詳細情報を表示
            tk.Label(frame, text=f"ID: {exercise[0]} | 種目名: {exercise[1]} | 説明: {exercise[2]}").pack(side="left")
            
            # 最新トレーニングデータ（セット数と日付）の取得
            cursor.execute("""
                SELECT sets, date FROM TrainingLog
                WHERE exercise_id = ?
                ORDER BY date DESC LIMIT 1
            """, (exercise[0],))
            latest_log = cursor.fetchone()
            
            if latest_log:
                latest_sets, latest_date = latest_log
                tk.Label(frame, text=f"最後にやった日: {latest_date} | セット数: {latest_sets}").pack(side="left")
            else:
                tk.Label(frame, text="最後のトレーニングデータなし").pack(side="left")

            # 進捗確認ボタン
            tk.Button(frame, text="進捗確認", command=lambda id=exercise[0]: show_progress(id)).pack(side="right")
            
            # トレーニングログ追加ボタン
            tk.Button(frame, text="ログ追加", command=lambda id=exercise[0]: add_training_log_for_exercise(id)).pack(side="right")
            
            # 種目削除ボタン
            def delete_exercise(exercise_id):
                """
                種目を削除する処理
                """
                try:
                    conn = sqlite3.connect("database.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Exercise WHERE id = ?", (exercise_id,))
                    cursor.execute("DELETE FROM TrainingLog WHERE exercise_id = ?", (exercise_id,))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("成功", "種目が削除されました！")
                    window.destroy()  # 削除後にウィンドウを更新
                except Exception as e:
                    messagebox.showerror("エラー", f"削除に失敗しました: {e}")

            tk.Button(frame, text="削除", command=lambda id=exercise[0]: delete_exercise(id)).pack(side="right")

    else:
        tk.Label(window, text="登録された種目がありません。").pack()

    tk.Button(window, text="閉じる", command=window.destroy).pack()


def add_training_log_for_exercise(exercise_id):
    """
    指定された種目IDに対してトレーニングログを追加するウィンドウ
    """
    def save_log():
        # セットごとにデータを保存
        date = entry_date.get()
        
        if date:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                
                for i in range(int(entry_sets.get())):  # セット数分ループ
                    weight = weights[i].get()
                    reps = reps_list[i].get()
                    
                    if weight and reps:
                        cursor.execute("""
                            INSERT INTO TrainingLog (exercise_id, weight, reps, sets, date) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (exercise_id, float(weight), int(reps), i+1, date))
                    else:
                        messagebox.showerror("エラー", "セットごとに重量と回数を入力してください！")
                        conn.close()
                        return

                conn.commit()
                conn.close()
                messagebox.showinfo("成功", "トレーニングログを追加しました！")
                window.destroy()
            except Exception as e:
                messagebox.showerror("エラー", f"データ保存に失敗しました: {e}")
        else:
            messagebox.showerror("エラー", "日付を入力してください！")

    def set_today_date():
        """
        現在の日付を入力欄に設定する
        """
        today = datetime.today().strftime('%Y-%m-%d')
        entry_date.delete(0, tk.END)
        entry_date.insert(0, today)

    window = tk.Toplevel()
    window.title("トレーニングログ追加")

    tk.Label(window, text="セット数:").pack()
    entry_sets = tk.Entry(window)
    entry_sets.pack()

    tk.Label(window, text="日付 (例: 2024-12-28):").pack()
    entry_date = tk.Entry(window)
    entry_date.pack()
    tk.Button(window, text="今日", command=set_today_date).pack(pady=5)

    def create_set_inputs():
        """
        ユーザーがセット数を入力した後にセットごとの重量と回数を入力するフィールドを横並びで作成
        """
        try:
            sets = int(entry_sets.get())
            if sets <= 0:
                raise ValueError("セット数は1以上でなければなりません")

            for widget in dynamic_widgets:
                widget.destroy()
            dynamic_widgets.clear()

            for i in range(sets):
                frame = tk.Frame(window)  # 新しいフレームを作成
                frame.pack(pady=5)

                tk.Label(frame, text=f"セット {i + 1} 重量 (kg):").pack(side="left")
                weight_entry = tk.Entry(frame)
                weight_entry.pack(side="left")
                weights.append(weight_entry)

                tk.Label(frame, text=f"セット {i + 1} 回数:").pack(side="left", padx=(10, 0))
                reps_entry = tk.Entry(frame)
                reps_entry.pack(side="left")
                reps_list.append(reps_entry)

        except ValueError:
            messagebox.showerror("エラー", "セット数は正の整数で入力してください！")

    tk.Button(window, text="セットの入力欄を作成", command=create_set_inputs).pack(pady=10)
    dynamic_widgets = []  # 動的に作成したウィジェットを格納するリスト
    weights = []  # 重量用の入力フィールドリスト
    reps_list = []  # 回数用の入力フィールドリスト

    tk.Button(window, text="保存", command=save_log).pack(pady=5)

def run_app():
    """
    メインアプリケーションを起動する
    """
    initialize_database()

    root = tk.Tk()
    root.title("筋トレログ管理アプリ")
    root.geometry("400x300")

    tk.Label(root, text="筋トレログ管理アプリ", font=("Arial", 16, "bold")).pack(pady=20)

    tk.Button(root, text="種目追加", command=add_exercise, font=("Arial", 14)).pack(pady=10)
    tk.Button(root, text="種目一覧を表示", command=show_exercise_list).pack(pady=10)
    tk.Button(root, text="終了", command=root.quit, font=("Arial", 14)).pack(pady=20)

    root.mainloop()
