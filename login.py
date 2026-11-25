import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageSequence
import mysql.connector


#database
DB_CONFIG = {"host": "localhost","user": "user","password": "sql123","database": "farmer"}


def connect_to_database():
    """Open a connection to the Farmer database."""
    return mysql.connector.connect(**DB_CONFIG)


#background
root = tk.Tk()
root.geometry("800x600")  # Same window size as login(2).py
root.title("Login / Register")
root.resizable(True, True)

animation_speed = 100
gif_frames = []
current_frame = 0
current_photo = None

try:
    gif_image = Image.open("background.gif")
    #keep the original frames so they can be resized to the current window.
    for frame in ImageSequence.Iterator(gif_image):
        gif_frames.append(frame.convert("RGBA").copy())
except FileNotFoundError:
    messagebox.showerror("Missing Background")
    root.destroy()
    raise


bg_label = tk.Label(root, bd=0)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)


def show_next_frame():
    """Resize each GIF frame to fill the window, then display it."""
    global current_frame, current_photo

    if not root.winfo_exists() or not gif_frames:
        return

    width = max(root.winfo_width(), 1)
    height = max(root.winfo_height(), 1)

    frame = gif_frames[current_frame].resize((width, height), Image.Resampling.LANCZOS)
    current_photo = ImageTk.PhotoImage(frame)
    bg_label.configure(image=current_photo)

    current_frame = (current_frame + 1) % len(gif_frames)
    root.after(animation_speed, show_next_frame)


#login
def login():
    entered_username = username_entry.get().strip()
    entered_password = password_entry.get().strip()

    if not entered_username or not entered_password:
        messagebox.showerror("Input Error", "Please enter your username and password.")
        return

    conn = None
    cursor = None
    try:
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account WHERE username = %s AND password = %s",(entered_username, entered_password))
        user = cursor.fetchone()

        if user:
            messagebox.showinfo("Login Successful", "Successfully logged in!")
            root.destroy()
            import project_final
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not log in:\n{err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


#registration
def register():
    """Register the username and password entered on the main screen."""
    new_username = username_entry.get().strip()
    new_password = password_entry.get().strip()

    if not new_username or not new_password:
        messagebox.showerror("Input Error","Enter a username and password in the fields above before registering.")
        return

    conn = None
    cursor = None
    try:
        conn = connect_to_database()
        cursor = conn.cursor()

        #check whether this username is already registered
        cursor.execute("SELECT username FROM account WHERE username = %s",(new_username,))
        existing_account = cursor.fetchone()

        if existing_account:
            messagebox.showerror("Already Registered","That username is already registered. Please log in or choose another username.")
            return

        #if it does not exist, create the account
        cursor.execute("INSERT INTO account (username, password) VALUES (%s, %s)",(new_username, new_password))
        conn.commit()

        messagebox.showinfo("Registration Successful","Your account has been created. You can now log in.")

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not register:\n{err}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()


#login screen ui
username_label = tk.Label(root, text="Username", bg="#333333", fg="#FFFFFF",font=("Arial", 16))
username_entry = tk.Entry(root, font=("Arial", 16), width=22)

password_label = tk.Label(root, text="Password", bg="#333333", fg="#FFFFFF",font=("Arial", 16))
password_entry = tk.Entry(root, font=("Arial", 16), show="*", width=22)

username_label.place(relx=0.5, rely=0.35, anchor="center")
username_entry.place(relx=0.5, rely=0.41, anchor="center")
password_label.place(relx=0.5, rely=0.53, anchor="center")
password_entry.place(relx=0.5, rely=0.59, anchor="center")

login_button = tk.Button(root, text="Login", bg="#333333", fg="#FFFFFF",activebackground="#4A4A4A", activeforeground="#FFFFFF",font=("Arial", 16), command=login,relief="raised", bd=2, highlightthickness=0)
login_button.place(relx=0.5, rely=0.70, x=-7, anchor="e", width=135, height=45)

register_button = tk.Button(root, text="Register", bg="#333333", fg="#FFFFFF",activebackground="#4A4A4A", activeforeground="#FFFFFF",font=("Arial", 16), command=register,relief="raised", bd=2, highlightthickness=0)
register_button.place(relx=0.5, rely=0.70, x=7, anchor="w", width=135, height=45)

username_entry.focus_set()
root.after(animation_speed, show_next_frame)
root.mainloop()
