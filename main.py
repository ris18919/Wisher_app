import base64
import os
import random
import shutil
import smtplib
import sqlite3
import subprocess
import sys
import threading
import time
import winreg
import hmac
import hashlib

from asynckivy import fade_transition
from docutils.utils.math.latex2mathml import letters
from dotenv import load_dotenv
from kivy.uix.textinput import TextInput
from kivy.core.audio import SoundLoader
from plyer import notification

from datetime import datetime, timedelta
from email.mime.text import MIMEText
from sched import scheduler

import pyautogui
import pystray
import requests
from PIL import Image
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from kivy.animation import Animation
from kivy.app import App
# from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import sp,dp
from kivy.properties import StringProperty, ListProperty, ColorProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
# from kivy.uix.popup import Popup
# from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition, FadeTransition, SwapTransition, SlideTransition, \
    WipeTransition
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from kivymd.uix.pickers import MDTimePickerDialHorizontal, MDModalDatePicker
from kivymd.uix.widget import MDWidget
from pystray import MenuItem as Item
from streamlit.cli_util import open_browser

from languages import LANGUAGES

my_email="rishabhjadonrishabh@gmail.com"
my_password="jstt sgha quei xjrk"
current_user={
    "id":None,
    "name":"",
    "email":"",
    "phone":"",
}
Window.fullscreen = False
Window.resizable = True
Window.size=(780,750)
Window.minimum_width = 780
Window.minimum_height = 750


LabelBase.register(name="RobotoFlex",
                   fn_regular="fonts/Roboto_Flex/RobotoFlex-VariableFont.ttf")
LabelBase.register(name="NotoSans",
                   fn_regular="fonts/Noto_Sans/NotoSans-VariableFont.ttf",)
LabelBase.register(name="NotoEmoji",
                   fn_regular="fonts/Noto_Emoji/NotoEmoji-VariableFont.ttf")
LabelBase.register(name="NotoColorEmoji",
                   fn_regular="fonts/Noto_Sans/Noto_Color_Emoji/NotoColorEmoji-Regular.ttf")
LabelBase.register(name="NotoSansDevanagari",
                   fn_regular="fonts/Noto_Sans_Devanagari/NotoSansDevanagari-VariableFont.ttf")

# ==================Database=========================

def initialize_database():

    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    phone TEXT,
    password TEXT,
    email_verification TEXT,
    phone_verification TEXT
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_session (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            is_logged_in INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wishes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    phone TEXT,
    recipient_email TEXT,
    message TEXT,
    subject TEXT,
    date TEXT,
    time TEXT,
    Platform TEXT,
    sent INTEGER DEFAULT 0,
    status TEXT,
    reminder_sent INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gmail_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT UNIQUE,
        token TEXT,
        refresh_token TEXT,
        token_uri TEXT,
        client_id TEXT,
        client_secret TEXT,
        scopes TEXT,
        expiry TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personalize(
    user_id INTEGER PRIMARY KEY,
    theme TEXT,
    language TEXT,
    font_size INTEGER,
    accent_color TEXT
    )"""
    )

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS advanced_settings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduler_status TEXT,
    scheduler_interval TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS general_settings(
        id INTEGER PRIMARY KEY,
        launch_startup INTEGER DEFAULT 0,
        minimize_tray INTEGER DEFAULT 0,
        auto_scheduler INTEGER DEFAULT 1,
        time_format TEXT DEFAULT '12-Hour',
        date_format TEXT DEFAULT 'DD/MM/YYYY',
        time_zone TEXT DEFAULT 'Asia/Kolkata'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notification_settings(
        id INTEGER PRIMARY KEY,
        enable_notification INTEGER DEFAULT 1,
        sound INTEGER DEFAULT 1,
        reminder TEXT
    )
    """)
    conn.commit()
    conn.close()

def show_popup(title, message):

    # dialog = None

    ok_button = MDButton(
        style="text",
        pos_hint={"center_x":0.5},
        theme_width="Custom",
        size_hint_x=None,
        width="70dp"
    )

    ok_button.add_widget(
        MDButtonText(
            text="OK",
            theme_text_color="Custom",
            text_color=(0,0,0,1),
            halign="center",
        )
    )

    dialog = MDDialog(

        MDDialogHeadlineText(
            text=title,
            halign="left",
        ),

        MDDialogSupportingText(
            text=message,
            theme_text_color="Custom",
            text_color=(0,0.4,1,1),
            halign="center"
        ),

        MDDialogButtonContainer(
            MDWidget(),
            ok_button,
            MDWidget(),
            spacing="0dp",

        ),

        md_bg_color=(1, 1, 1, 1),
    )

    ok_button.bind(
        on_release=lambda *args: dialog.dismiss()
    )

    dialog.open()

class HoverButton(Button):
    hovered=BooleanProperty(False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def get_screen(self):
        widget=self.parent
        while widget is not None:
            if isinstance(widget,Screen):
                return widget
            widget=widget.parent
        return None

    def on_mouse_pos(self,*args):

        if not self.get_root_window():
            return

        screen = self.get_screen()

        # Do not react while this button's screen is inactive
        if screen and screen.manager:
            if screen.manager.current!=screen.name:
                self.reset_hover()
                return


        pos=args[1]
        inside = self.collide_point(
            *self.to_widget(*pos)
        )

        if self.hovered == inside:
            return

        self.hovered=inside

        if inside:
            Window.set_system_cursor("hand")
        else:
            Window.set_system_cursor("arrow")

    def reset_hover(self):
        self.hovered = False
        Window.set_system_cursor("arrow")

    def on_parent(self,instance,parent):
        if parent is None:
            Window.unbind(mouse_pos=self.on_mouse_pos)
            self.reset_hover()


class FlashScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.loading_event = None

    def on_enter(self,*args):
        Clock.schedule_once(
            self.initialize_flash_screen,
            0
        )

    def initialize_flash_screen(self,dt):
        self.background_animate()
        self.ids.progress_bar.value = 0

        self.loading_event = Clock.schedule_interval(
            self.update_loading,
            0.05
        )

    def background_animate(self):
        background_logo = self.ids.background_logo
        Animation.cancel_all(background_logo)
        background_logo.opacity = 0
        anim=(Animation(
            opacity=1,
            duration=0.8,
            t="out_quad"

        ))
        anim.bind(
            on_complete=lambda *args:self.animate_logo()
        )

        anim.start(background_logo)

    def animate_logo(self):
        splash_logo = self.ids.splash_logo
        Animation.cancel_all(splash_logo)
        splash_logo.opacity = 0
        anim=Animation(
            opacity=1,
            duration=1.5,
            t="out_quad"

        )
        anim.bind(on_complete=lambda *args:self.splash_label_animate())
        anim.start(splash_logo)


    def splash_label_animate(self):

        w=self.ids.letter_w
        letters=[
            self.ids.letter_i,
            self.ids.letter_s,
            self.ids.letter_h,
            self.ids.letter_e,
            self.ids.letter_r
        ]

        # Final positions
        final_positions = [
            dp(115),  # i
            dp(140),  # s
            dp(165),  # h
            dp(190),  # e
            dp(215)  # r
        ]

        # W final position
        final_w_x = dp(85)

        # -----------------------------
        # W starts slightly to right
        # -----------------------------
        start_w_x = dp(105)
        # reset W
        Animation.cancel_all(w)
        w.opacity = 1
        w.x=start_w_x

        # All other letters start exactly behind W
        for letter in letters:
            Animation.cancel_all(letter)
            letter.opacity = 0
            letter.x=start_w_x

        # Move W slightly left while first letter comes out
        delay = 0
        for letter, final_x in zip(letters, final_positions):
            def animate_letter(dt, widget=letter, x=final_x):
                # Move W left
                Animation(
                    x=final_w_x,
                    duration=0.5,
                    t="out_cubic"
                ).start(w)

                # Bring letter out from behind W
                Animation(
                    x=x,
                    opacity=1,
                    duration=0.5,
                    t="out_cubic"
                ).start(widget)

            Clock.schedule_once(animate_letter, delay)

            delay += 0.25



    def update_loading(self, _dt):

        self.ids.progress_bar.value += 1

        if self.ids.progress_bar.value >= self.ids.progress_bar.max:
            self.loading_event.cancel()
            app=App.get_running_app()
            if app.restore_login():
                self.manager.current = "home"
            else:
                self.manager.current = "login"

            return False

        return True

class LoginScreen(Screen):

    def toggle_password(self):
        password_field=self.ids.login_password
        visibility_btn=self.ids.visibility_btn

        password_field.password= not password_field.password
        if password_field.password:
            visibility_btn.background_normal="image/visibility_off_30.png"
            visibility_btn.background_down="image/visibility_off_30.png"
        else:
            visibility_btn.background_normal="image/visibility_on_30.png"
            visibility_btn.background_down="image/visibility_on_30.png"

    def signin_user(self):
        conn1=sqlite3.connect("user.db")
        cursor1=conn1.cursor()

        personalize = self.manager.get_screen("personalize")
        global current_user
        email=self.ids.login_email.text
        phone=self.ids.login_email.text
        password=self.ids.login_password.text
        # Empty Field Check
        if not email or not password:
            show_popup(title="required",message="Please fill all fields")
            return

        # Database Check
        cursor1.execute("SELECT * FROM users WHERE email=? or phone=?",(email,phone))
        user = cursor1.fetchone()


        if user is None:
            show_popup(title="error",message="User does not exist. Please Sign Up")
            return

        # check password
        if password != user[4]:
            show_popup(title="error",message="Password is Wrong")
            return
        print("Login Successful")
        current_user["id"]=user[0]
        current_user["email"]=user[2]
        current_user["phone"]=user[3]
        current_user["name"]=user[1]

        conn22=sqlite3.connect("user.db")
        cursor22=conn22.cursor()
        cursor22.execute("""
            INSERT OR REPLACE INTO login_session
            (id, user_id, is_logged_in)
            VALUES (1, ?, 1)
        """, (current_user["id"],))

        conn22.commit()
        conn22.close()

        self.ids.login_email.text = ""
        self.ids.login_password.text = ""
        self.manager.current = "welcome"
        personalize.load_settings()



    def start_google_login(self):
        threading.Thread(
            target=self.google_signin,
            daemon=True
        ).start()

    def google_signin(self):
        global current_user
        try:
            conn2=sqlite3.connect("user.db")
            cursor2=conn2.cursor()
            flow=InstalledAppFlow.from_client_secrets_file("client_secret.json",
                                                           scopes=[
                                                               "openid",
                                                               "https://www.googleapis.com/auth/userinfo.email",
                                                               "https://www.googleapis.com/auth/userinfo.profile",
                                                               "https://www.googleapis.com/auth/user.phonenumbers.read"
                                                           ]
                                                           )
            creds=flow.run_local_server(port=0)
            if not creds:
                conn2.close()
                Clock.schedule_once(
                    lambda dt:setattr(
                        self.manager,
                        "current",
                        "login"
                    )
                )
                return

            id_info = id_token.verify_oauth2_token(
                creds.id_token,
                Request()
            )
            response=requests.get("https://people.googleapis.com/v1/people/me?",
                                  headers={"Authorization": f"Bearer {creds.token}"
                                           }
                                  )
            response.json()
            name=id_info.get("name","")
            email=id_info.get("email","")

            cursor2.execute("""
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                password TEXT           
                )
                """)

            #Save into database
            cursor2.execute("SELECT * FROM users WHERE email=?",(email,)
                           )
            user = cursor2.fetchone()

            if user is None:
                cursor2.execute("""
                                INSERT INTO users(name, email, phone, password) VALUES(?,?,?,?)""",
                                (name, email, "", "")
                                )
                conn2.commit()


            else:
                cursor2.execute("""
                                UPDATE users SET name=?,email=? WHERE email=?""", (name, email, email)
                                )
                conn2.commit()
                #
            cursor2.execute("SELECT * FROM users WHERE email=?",(email,))
            user = cursor2.fetchone()

            # store current user
            current_user["id"] = user[0]
            current_user["name"] = user[1]
            current_user["email"] = user[2]
            current_user["phone"] = user[3]

            conn2.close()

            print("Google Login Successful")
            conn24 = sqlite3.connect("user.db")
            cursor24 = conn24.cursor()
            cursor24.execute("""
                        INSERT OR REPLACE INTO login_session
                        (id, user_id, is_logged_in)
                        VALUES (1, ?, 1)
                    """, (current_user["id"],))

            conn24.commit()
            conn24.close()
            Clock.schedule_once(
                lambda dt: setattr(
                    self.manager,
                    "current",
                    "welcome"
                )
            )

        except Exception as e:
            print("Google Login Cancelled or Failed",e)



class SignUpScreen(Screen):

    def toggle_password(self):
        password_field=self.ids.signup_password
        visibility_btn=self.ids.signup_visibility

        password_field.password= not password_field.password
        if password_field.password:
            visibility_btn.background_normal="image/visibility_off_30.png"
            visibility_btn.background_down="image/visibility_off_30.png"
        else:
            visibility_btn.background_normal="image/visibility_on_30.png"
            visibility_btn.background_down="image/visibility_on_30.png"

    def signup_user(self):
        conn1=sqlite3.connect("user.db")
        cursor1=conn1.cursor()

        name=self.ids.signup_name.text
        email=self.ids.signup_email.text.strip().lower()
        phone=self.ids.signup_phone.text
        password=self.ids.signup_password.text
        # Empty field check
        if name=="" and email=="" and phone=="" and password=="":
            show_popup(title="required",message="Please fill all fields")
            return

        cursor1.execute("SELECT * FROM users WHERE email=?",(email,))
        existing = cursor1.fetchone()
        if existing:
            show_popup(title="",message="Email already exists")
            self.ids.signup_name.text = ""
            self.ids.signup_email.text = ""
            self.ids.signup_phone.text = ""
            self.ids.signup_password.text = ""
        else:
            (cursor1.execute
             ("INSERT INTO users (name, email, phone, password) VALUES(?,?,?,?)",(name,email,phone,password)
                ))
            conn1.commit()
            show_popup(title="",message="Signup Successful")
            self.manager.current = "login"
            self.ids.signup_name.text = ""
            self.ids.signup_email.text = ""
            self.ids.signup_phone.text = ""
            self.ids.signup_password.text = ""

    def start_google_signup(self):
        threading.Thread(target=self.google_signup,daemon=True).start()

    def google_signup(self):
        try:
            flow=InstalledAppFlow.from_client_secrets_file("client_secret.json",
                                                           scopes=[
                                                               "openid",
                                                               "https://www.googleapis.com/auth/userinfo.email",
                                                               "https://www.googleapis.com/auth/userinfo.profile"
                                                           ]
                                                           )
            creds=flow.run_local_server(port=0)
            if not creds:
                return

            response=requests.get("https://www.googleapis.com/oauth2/v2/userinfo",
                                  headers={"Authorization": f"Bearer {creds.token}"
                                    }
                                    )
            user_info=response.json()
            name=user_info.get("name","")
            email=user_info.get("email","")


            conn1=sqlite3.connect("user.db")
            cursor1=conn1.cursor()
            cursor1.execute("""
            CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            password TEXT
            )""")

            # save into database
            cursor1.execute("SELECT * FROM users WHERE email=?",(email,))

            existing_user = cursor1.fetchone()
            if not existing_user:
                cursor1.execute("""
                INSERT INTO users (name, email, phone, password)
                VALUES(?,?,?,?)""",
                               (
                                   name,
                                   email,
                                   "",
                                   "",
                               )
                )
                conn1.commit()
                Clock.schedule_once(
                lambda dt:show_popup(title="",message="Signup Successful")
                )
                current_user["name"]=name
                current_user["email"]=email
                self.manager.current="login"
            else:
                current_user["name"]=name
                current_user["email"]=email
                Clock.schedule_once(
                lambda dt:show_popup(title="error",message="username already exists\n Signing in...")
                )
                Clock.schedule_once(
                    lambda dt: setattr(
                        self.manager,
                        "current",
                        "welcome"
                    )
                )
            conn1.close()
        except Exception as e:
            show_popup(title="Google signup error",message=e)
            self.manager.current = "signup"



class ForgotPasswordScreen(Screen):
    generated_otp=""
    otp_expiry = None
    timer_event=None
    tim= int(30)

    def toggle_password(self):
        password_field=self.ids.new_password
        visibility_btn=self.ids.new_visibility

        password_field.password= not password_field.password
        if password_field.password:
            visibility_btn.background_normal="image/visibility_off_30.png"
            visibility_btn.background_down="image/visibility_off_30.png"
        else:
            visibility_btn.background_normal="image/visibility_on_30.png"
            visibility_btn.background_down="image/visibility_on_30.png"

    def send_otp(self):

        email=self.ids.fp_email.text
        if not email:
            show_popup(title="",message="Enter your email")
            return

        self.generated_otp=str(random.randint(10000,99999))
        print(f"OTP: {self.generated_otp}")

        #send email
        with smtplib.SMTP("smtp.gmail.com",587) as connection:
            connection.starttls()
            connection.login(user=my_email,password=my_password)
            connection.sendmail(from_addr=my_email,
                                to_addrs=email,
                                msg=f"""Subject:OTP Verification\n
                                Your OTP is {str(self.generated_otp)}
                                This OTP will expire in 30 seconds."""
                                )
            show_popup(title="Sent", message="OTP sent")

        self.otp_expiry=datetime.now()+timedelta(seconds=int(30))
        self.ids.otp_input_box.opacity = 1
        self.ids.otp_input.disabled = False

        self.ids.verify_btn.opacity = 1
        self.ids.verify_btn.disabled = False
        self.start_resend_timer()


    def verify_otp(self):
        entered_otp=self.ids.otp_input.text

        if datetime.now()>self.otp_expiry:
            show_popup(title="",message="OTP expired\nPlease resend OTP")
            self.ids.resend_btn.opacity = 1
            self.ids.resend_btn.disabled = False
            self.ids.resend_btn.text = f"Resend OTP"

        elif entered_otp==self.generated_otp:
            show_popup(title="OTP Verification",message="Email Verified Successfully")

            self.ids.fp_password.opacity = 1
            self.ids.fp_password.disabled = False

            self.ids.fp_reset_btn.opacity = 1
            self.ids.fp_reset_btn.disabled = False
        else:
            show_popup(title="OTP Verification",message="Invalid OTP")

    def start_resend_timer(self):
        self.tim=30
        self.ids.resend_btn.disabled = True
        self.ids.resend_btn.text = f"Resend OTP ({self.tim}s)"
        if self.timer_event:
            self.timer_event.cancel()

        self.timer_event=Clock.schedule_interval(
            self.update_timer,
            1
        )
    def update_timer(self,_dt):
        self.tim-=1
        self.ids.resend_btn.text = (
            f"Resend OTP ({self.tim}s)"
        )
        if self.tim <= 0:
            self.ids.resend_btn.text="Resend OTP"
            self.ids.resend_btn.disabled = False
            if self.timer_event:
                self.timer_event.cancel()
            return False
        return True

    def resend_otp(self):
        self.send_otp()
        self.start_resend_timer()



    def reset_password(self):
        conn=sqlite3.connect("user.db")
        cursor=conn.cursor()

        email = self.ids.fp_email.text.strip()
        new_password = self.ids.new_password.text.strip()

        if  email=="" or new_password == "":
            show_popup("required", "⚠ Please fill all fields")
            return

        # check user exists
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if not user:
            show_popup("Error", "User not found")
            return

        # update password
        cursor.execute(
            "UPDATE users SET password=? WHERE email=?",
            (new_password,email)
        )
        conn.commit()
        conn.close()
        show_popup("Success", "Password updated")
        self.manager.current = "login"
        self.ids.fp_email.text=""
        self.ids.new_password.text=""
        self.ids.otp_input.text=""

class DateTextInput(TextInput):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            screen = app.root.get_screen("add_wish")

            screen.date_picker()

            return True

        return super().on_touch_down(touch)

class TimeTextInput(TextInput):

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            screen = app.root.get_screen("add_wish")

            screen.time_picker()

            return True

        return super().on_touch_down(touch)

class AddWishScreen(Screen):

    selected_platforms = StringProperty("")
    side_panel_color = ColorProperty((0.176, 0.106, 0.306, 1))

    def refresh_language(self):
        t = App.get_running_app().language.translate
        self.ids.gmail_btn.text=t("Connect Gmail")
        self.ids.home.text = t("Home")
        self.ids.add.text=t("Add Wish")
        self.ids.history.text=t("Wish History")
        self.ids.personalize.text=t("Personalize")
        self.ids.setting.text = t("Settings")
        self.ids.logout.text = t("Logout")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.open_menu = False
        self.dialog = None

    def open_platform_dialog(self):

        content = Factory.PlatformDialogContent()

        ok_btn = MDButton(style="filled")
        ok_btn.add_widget(
            MDButtonText(
                text="OK"
            )
        )

        cancel_btn = MDButton(style="text")
        cancel_btn.add_widget(
            MDButtonText(
                text="Cancel"
            )
        )

        self.dialog = MDDialog(
            MDDialogHeadlineText(
              text="Select Platform",
              halign="center",
            ),
            content,
            MDDialogButtonContainer(
                cancel_btn,
                MDWidget(),
                ok_btn,
            ),

            md_bg_color=(1, 1, 1, 1),
        )

        ok_btn.bind(
            on_release=lambda x: self.update_platform_text(content)
        )

        cancel_btn.bind(
            on_release=lambda x: self.dialog.dismiss()

        )
        # self.dialog.bind(
        #     on_dismiss=self.platform_dialog_dismissed
        # )

        self.dialog.open()
        #self.ids.arrow_image.icon="chevron-up"

    def platform_dialog_dismissed(self,*args):
        self.ids.arrow_image.icon="chevron-down"

    def on_enter(self):
        self.check_gmail_connection()
        self.reset_hover_buttons()

    def on_leave(self, *args):
        self.reset_hover_buttons()

    def reset_hover_buttons(self):
        for widget in self.walk():
            if isinstance(widget, HoverButton):
                widget.reset_hover()

    def check_gmail_connection(self):

        user_email = current_user["email"]

        conn20 = sqlite3.connect("user.db")
        cursor20 = conn20.cursor()

        cursor20.execute("""
            SELECT 1
            FROM gmail_tokens
            WHERE user_email = ?
            LIMIT 1
        """, (user_email,))

        row = cursor20.fetchone()

        conn20.close()

        if row:
            self.ids.gmail_btn.text = "Gmail Connected"
            self.ids.gmail_btn.disabled = True
        else:
            self.ids.gmail_btn.text = "Connect Gmail"
            self.ids.gmail_btn.disabled = False

    def connect_gmail(self):
        user_email = current_user["email"]
        conn20=sqlite3.connect("user.db")
        cursor20=conn20.cursor()
        cursor20.execute(
            "SELECT * FROM gmail_tokens WHERE user_email=?",(user_email,)
        )
        row=cursor20.fetchone()

        conn20.close()
        gmail_btn=self.ids.gmail_btn
        if row is not None:
            # gmail already connected
            gmail_btn.text="Gmail Connected"
            gmail_btn.disabled = True
            return
        gmail_btn.disabled = True
        gmail_btn.text = "Connecting..."

        # Run Oauth in background thread
        thread=threading.Thread(target=self.gmail_oauth_thread, args=(user_email,),daemon=True).start()
        # Watchdog: reset UI if OAuth doesn't finish
        # self._gmail_timeout_event = Clock.schedule_once(
        #     self.gmail_connection_timeout,
        #     5
        # )

    def gmail_oauth_thread(self,user_email):
        success=save_credentials(user_email)
        # Return to kivy main thread
        Clock.schedule_once(
            lambda dt:self.gmail_oauth_finished(success),
            0
        )

    def gmail_oauth_finished(self,success):

        # Cancel watchdog
        # if hasattr(self, "_gmail_timeout_event"):
        #     self._gmail_timeout_event.cancel()
        #     self._gmail_timeout_event = None

        gmail_btn=self.ids.gmail_btn
        if success:
            gmail_btn.text = "Gmail Connected"
            gmail_btn.disabled = True
            print("Gmail connected successfully")
        else:
            gmail_btn.text = "Connect Gmail"
            gmail_btn.disabled = False
            show_popup(
                title="Gmail Connection",message="Gmail connection was cancelled.\n"
                                                 "Please try again."
            )

    # def gmail_connection_timeout(self, dt):
    #
    #     gmail_btn = self.ids.gmail_btn
    #
    #     # Reset button
    #     gmail_btn.text = "Connect Gmail"
    #     gmail_btn.disabled = False
    #
    #     self._gmail_timeout_event = None
    #
    #     show_popup(
    #         title="Gmail Connection",
    #         message="Gmail connection was cancelled or timed out.\n"
    #                 "Please try again."
    #     )

    def email_checkbox(self,checkbox,active):

        if not active:
            return
        user_email=current_user["email"]
        if not user_email:
            checkbox.active = False
            show_popup(
                title="Gmail Not Connected",
                message="Gmail Not Connected.\n"
                        "Please connect your Gmail from side menu."
            )
            return
        conn21=sqlite3.connect("user.db")
        cursor21=conn21.cursor()
        cursor21.execute(
            """SELECT 1 FROM gmail_tokens WHERE user_email=? LIMIT 1""",(user_email,)
                         )
        row=cursor21.fetchone()
        conn21.close()
        if row is None:
            checkbox.active=False
            show_popup(
                title="",
                message="Gmail is not connected.\n"
                       "Please connect your gmail from side menu."
            )
            return

    def sms_checkbox(self):
        check_box=self.ids.sms_cb
        check_box.active=not check_box.active
        if check_box.active:
            self.ids.mode.text=self.selected_platforms
        else:
            self.ids.mode.text="Select Platform"

    def whatsapp_checkbox(self):
        check_box=self.ids.whatsapp_cb
        check_box.active=not check_box.active
        if check_box.active:
            self.ids.mode.text=self.selected_platforms
        else:
            self.ids.mode.text="Select Platform"

    def update_platform_text(self,content):
        selected_platform = []
        if content.ids.email_cb.active:
            selected_platform.append("Email")
        if content.ids.sms_cb.active:
            selected_platform.append("SMS")
        if content.ids.whatsapp_cb.active:
            selected_platform.append("WhatsApp")

        if selected_platform:
            self.selected_platforms=",".join(selected_platform)
        else:
            self.selected_platforms="Select Platform"
        self.ids.mode.text=self.selected_platforms
        self.dialog.dismiss()

    def date_picker(self):
        picker=MDModalDatePicker()
        picker.bind(on_ok=self.set_date,
                    on_cancel=self.on_date_cancel)
        picker.open()

    def set_date(self,instance_date_picker):
        date=instance_date_picker.get_date()
        if date:
            actual_date=date[0]
            formatted_date=actual_date.strftime("%Y-%m-%d")
            self.ids.wish_date.text=formatted_date
        instance_date_picker.dismiss()

    def on_date_cancel(self,instance_date_picker):
        instance_date_picker.dismiss()

    def time_picker(self):
        picker=MDTimePickerDialHorizontal()
        picker.bind(on_ok=self.set_time,
                    on_cancel=self.on_time_cancel)
        picker.open()

    def set_time(self,instance_time_picker):
        tim=instance_time_picker.time
        if tim:
            actual_time=tim
            formatted_time=actual_time.strftime("%H:%M:%S %p")
            self.ids.wish_time.text=formatted_time
        instance_time_picker.dismiss()

    def on_time_cancel(self,instance_time_picker):
        instance_time_picker.dismiss()

    def close_side_menu(self):
        if self.open_menu:
            self.side_menu()

    def side_menu(self):
        menu_btn=self.ids.menu_btn
        side_panel=self.ids.side_panel
        over_lay=self.ids.overlay
        if not self.open_menu:
            over_lay.disabled = False
            over_lay.opacity=0
            over_lay.size_hint_x=1
            over_lay.size_hint_y=1
            side_panel.disabled = False

            # Cancel previous animations
            Animation.cancel_all(over_lay)
            Animation.cancel_all(side_panel)

            Animation(
                opacity=1,
                duration=0.25,

            ).start(over_lay)
            Animation(
                opacity=1,
                x=0,
                duration=0.3,
                t="out_cubic"
            ).start(side_panel)
            menu_btn.background_normal="image/close.png"
            menu_btn.background_down="image/close.png"
            self.open_menu=True

        else:

            # Cancel previous animations
            Animation.cancel_all(over_lay)
            Animation.cancel_all(side_panel)

            Animation(
                opacity=0,
                duration=0.25,
            ).start(over_lay)
            Animation(
                opacity=0,
                x=-side_panel.width,
                duration=0.3,
                t="in_cubic"
            ).start(side_panel)

            over_lay.disabled = True
            over_lay.opacity=0
            over_lay.size_hint_x=0
            over_lay.size_hint_y=0
            side_panel.disabled = True
            menu_btn.background_normal="image/menu.png"
            menu_btn.background_down="image/menu.png"
            self.open_menu=False

    def schedule_wish(self):
        conn=sqlite3.connect("user.db")
        cursor=conn.cursor()

        mode=self.ids.mode.text
        name = self.ids.wish_name.text.strip()
        phone = self.ids.wish_phone.text.strip()
        recipient_email=self.ids.wish_email.text.strip()
        message = self.ids.wish_message.text.strip()
        subject=self.ids.wish_subject.text.strip()
        date = self.ids.wish_date.text.strip()
        tim = self.ids.wish_time.text.strip()

        if not all([name, phone,recipient_email, message, date, tim]):
            show_popup("required", "⚠ Fill all fields")
            return

        elif not mode == self.selected_platforms:
            show_popup(title="required",message="Select Platform")
            return

        #validate date and time
        try:
            datetime.strptime(f"{date} {tim}","%Y-%m-%d %H:%M:%S %p")

        except ValueError as e:
            show_popup(title="invalid",message=f"invalid date/time format {e}")
            return

        # Save wish
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wishes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id,
        name TEXT,
        phone TEXT,
        recipient_email TEXT,
        message TEXT,
        subject TEXT,
        date TEXT,
        time TEXT,
        Platform TEXT,
        sent INTEGER DEFAULT 0,
        status TEXT
        )
        """)

        cursor.execute(
            "INSERT INTO wishes(user_id,name,phone,recipient_email,message,subject,date,time,Platform) VALUES(?,?,?,?,?,?,?,?,?)",
            (current_user["id"],name, phone,recipient_email,message,subject, date, tim, mode)
        )

        conn.commit()

        show_popup("Success", "Wish Scheduled")
        self.ids.wish_name.text=""
        self.ids.wish_phone.text=""
        self.ids.wish_email.text=""
        self.ids.wish_message.text=""
        self.ids.wish_subject.text=""
        self.ids.wish_date.text=""
        self.ids.wish_time.text=""

        self.ids.mode.text="Select Platform"


class WelcomeScreen(Screen):

    def on_enter(self,*args):
        self.reset_hover_buttons()
        text_image = self.ids.text_image

        # Cancel any previous scheduled transition
        if hasattr(self, "_welcome_event") and self._welcome_event:
            self._welcome_event.cancel()
            self._welcome_event=None

        # Fade in animation
        anim = Animation(opacity=1, duration=1.3,t="out_quad")

        # Cancel previous animation
        Animation.cancel_all(text_image, "opacity")

        anim.start(text_image)

        # Schedule Only one Transition
        self._welcome_event=Clock.schedule_once(self.go_next, 2.5)

    def on_leave(self, *args):
        self.reset_hover_buttons()
        if hasattr(self,"_welcome_event") and self._welcome_event:
            self._welcome_event.cancel()
            self._welcome_event=None
        Animation.cancel_all(self.ids.text_image, "opacity")

    def reset_hover_buttons(self):
        for widget in self.walk():
            if isinstance(widget, HoverButton):
                widget.reset_hover()

    def go_next(self,_dt):
        self._welcome_event=None
        app=App.get_running_app()
        if app.restore_login():
            self.manager.current = "home"
        else:
            self.manager.current = "login"

class ProfileSpinnerOption:
    pass

class HomeScreen(Screen):
    profile_bg = ListProperty([0, 0, 0, 0])
    side_panel_color = ColorProperty((0.176, 0.106, 0.306, 1))

    def refresh_language(self):
        t = App.get_running_app().language.translate

        self.ids.home.text = t("Home")
        self.ids.add.text=t("Add Wish")
        self.ids.history.text=t("Wish History")
        self.ids.personalize.text=t("Personalize")
        self.ids.setting.text = t("Settings")
        self.ids.logout.text = t("Logout")

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.rect = None
        self.menu_open = False

    def logout(self):
        conn24 = sqlite3.connect("user.db")
        cursor24 = conn24.cursor()

        cursor24.execute("""
                UPDATE login_session
                SET is_logged_in=0
                WHERE user_id=?
            """,(current_user["id"],))

        conn24.commit()
        # conn24.close()

        # Clear current user
        current_user.clear()

        self.manager.current = "login"

    def close_side_menu(self):
        if self.menu_open:
            self.side_menu()

    def side_menu(self):
        menu_btn=self.ids.menu_btn
        side_panel=self.ids.side_panel
        over_lay=self.ids.overlay

        if not self.menu_open:
            side_panel.disabled = False
            over_lay.disabled = False
            over_lay.size_hint_x=1
            over_lay.size_hint_y=1
            Animation(
                opacity=1,
                duration=0.25,

            ).start(over_lay)
            # animation side panel
            Animation(
                opacity=1,
                x=0,
                duration=0.3,
                t="out_cubic"
            ).start(side_panel)
            # change icon
            menu_btn.background_normal="image/close.png"
            menu_btn.background_down="image/close.png"
            self.menu_open = True
        else:

            Animation(
                opacity=0,
                duration=0.25,
            ).start(over_lay)
            # animation side panel
            Animation(
                opacity=0,
                x=-side_panel.width,
                duration=0.3,
                t="in_cubic"
            ).start(side_panel)
            side_panel.disabled = True
            over_lay.size_hint_x=0
            over_lay.size_hint_y=0
            over_lay.disabled = True
            self.menu_open = False
            menu_btn.background_normal="image/menu.png"
            menu_btn.background_down="image/menu.png"

    def on_pre_enter(self, *args):
        Clock.schedule_once(self.load_home_data,0)
        self.ids.overlay.opacity = 0
        self.ids.overlay.disabled = True
        self.ids.side_panel.opacity = 0
        self.ids.side_panel.disabled = True
        self.menu_open = False


    def load_home_data(self,_dt):
        self.total_wishes()
        self.pending_wishes()
        self.sent_wishes()
        self.failed_wishes()


    def total_wishes(self):
        try:
            conn8 = sqlite3.connect("user.db")
            cursor8 = conn8.cursor()
            cursor8.execute("SELECT COUNT(*) FROM wishes WHERE user_id=?", (current_user["id"],))
            total = cursor8.fetchone()[0]
            self.ids.wish_number.text=str(total)
        except Exception as e:
            print(e)
    def pending_wishes(self):
        try:
            conn9=sqlite3.connect("user.db")
            cursor9=conn9.cursor()
            cursor9.execute("""SELECT COUNT(*) FROM wishes WHERE status='Pending' and user_id=?""", (current_user["id"],))
            total=cursor9.fetchone()[0]
            self.ids.pending_number.text=str(total)
        except Exception as e:
            print(e)

    def sent_wishes(self):
        try:
            conn10=sqlite3.connect("user.db")
            cursor10=conn10.cursor()
            cursor10.execute("SELECT COUNT(*) FROM wishes WHERE status='Success' and user_id=?", (current_user["id"],))
            total=cursor10.fetchone()[0]
            self.ids.sent_number.text=str(total)
        except Exception as e:
            print(e)

    def failed_wishes(self):
        try:
            conn11=sqlite3.connect("user.db")
            cursor11=conn11.cursor()
            cursor11.execute("SELECT COUNT(*) FROM wishes WHERE status='Failed' and user_id=?", (current_user["id"],))
            total=cursor11.fetchone()[0]
            self.ids.failed_number.text=str(total)
        except Exception as e:
            print(e)

    def on_enter(self,*args):

        self.reset_hover_buttons()
        full_name = str(current_user["name"]).split()
        first_name = full_name[0]
        home_label = self.ids.home_label
        home_label.text=f"Welcome, {first_name}"
        self.ids.profile.text=first_name

    def on_leave(self, *args):
        self.reset_hover_buttons()

    def reset_hover_buttons(self):
        for widget in self.walk():
            if isinstance(widget, HoverButton):
                widget.reset_hover()

    def on_spinner_select(self, text):
        if text == "Edit Profile":

            # Safely switch screens without weak reference crashes
            self.manager.current = "edit_profile"

class EditProfileScreen(Screen):
    generated_otp = ""
    otp_expiry = None
    timer_event = None
    tim = int(30)

    def on_pre_enter(self,*args):
        self.ids.full_name.text = current_user["name"]
        self.ids.email.text = current_user["email"]
        self.ids.phone.text = current_user["phone"]

    def verify_email(self):
        self.generated_otp = str(random.randint(10000, 99999))
        print(f"OTP: {self.generated_otp}")

        # send email
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=my_password)
            connection.sendmail(from_addr=my_email,
                                to_addrs=self.ids.email.text,
                                msg=f"""Subject:OTP Verification\n
                                        Your OTP is {str(self.generated_otp)}
                                        This OTP will expire in 30 seconds."""
                                )
            show_popup(title="Sent", message="OTP sent")

        self.otp_expiry = datetime.now() + timedelta(seconds=int(30))
        self.ids.verify.opacity=0
        self.ids.verify.disabled = True
        self.ids.OTP.opacity = 1
        self.ids.OTP.disabled = False

        self.start_resend_timer()


    def verify_otp(self,entered_otp):
        # entered_otp=self.ids.OTP.text

        if datetime.now()>self.otp_expiry:
            show_popup(title="",message="OTP expired\nPlease Verify again.")
            self.ids.OTP.opacity=0
            self.ids.OTP.disabled = True
            self.ids.verify.opacity = 1
            self.ids.verify.disabled = False
            self.ids.verify.text = f"Verify"

        elif entered_otp==self.generated_otp:
            show_popup(title="OTP Verification",message="Email Verified Successfully")

            # self.ids.fp_password.opacity = 1
            # self.ids.fp_password.disabled = False
            #
            # self.ids.fp_reset_btn.opacity = 1
            # self.ids.fp_reset_btn.disabled = False
            self.ids.OTP.opacity = 0
            self.ids.OTP.disabled = False
            self.ids.verified.opacity = 1
            self.ids.verified.text="Verified"
            self.ids.verified.color= 0.13, 0.55, 0.25, 1
        else:
            show_popup(title="OTP Verification",message="Invalid OTP")
    def start_resend_timer(self):
        self.tim=30
        self.ids.verify.disabled = True
        self.ids.verify.text = f"Verify ({self.tim}s)"
        if self.timer_event:
            self.timer_event.cancel()

        self.timer_event=Clock.schedule_interval(
            self.update_timer,
            1
        )
    def update_timer(self,_dt):
        self.tim-=1
        self.ids.verify.text = (
            f"Verify ({self.tim}s)"
        )
        if self.tim <= 0:
            self.ids.verify.text="Verify"
            self.ids.verify.disabled = False
            if self.timer_event:
                self.timer_event.cancel()
            return False
        return True

    def update_profile(self):

        name = self.ids.full_name.text.strip()
        email = self.ids.email.text.strip()
        phone = self.ids.phone.text.strip()
        email_verification = self.ids.verified.text.strip()

        conn7 = sqlite3.connect("user.db")
        cursor7 = conn7.cursor()

        cursor7.execute("""
        UPDATE users
        SET
            name=?,
            email=?,
            phone=?
        WHERE id=?
        """,
        (
            name,
            email,
            phone,
            current_user["id"]
        ))

        conn7.commit()
        conn7.close()

        current_user["name"] = name
        current_user["email"] = email
        current_user["phone"] = phone

        # Update the profile button on the Home screen
        home = App.get_running_app().root.get_screen("home")
        home.ids.profile.text = name.split()[0] if name else "Profile"

        show_popup("Success", "Profile updated successfully.")

        self.manager.current = "home"


class LanguageManager(EventDispatcher):
    current_language=StringProperty("English")
    def translate(self,key):
        return LANGUAGES[self.current_language].get(key,key)

language_manager = LanguageManager()

class PersonalizeScreen(Screen):
    selected_theme=StringProperty()
    outer_container_color=ColorProperty(
        (1,1,1,.15)
    )
    content_container_color=ColorProperty(
        (0.91, 0.831, 0.969, 1.0)
    )
    palette_container_color=ColorProperty(
        (1,1,1,1)
    )
    track_container_color=ColorProperty(
        (0,0,0,1)
    )
    line_container_color=ColorProperty(
        (1,1,1,1)
    )


    def toggle_language(self):
        language_options=self.ids.language_options
        parent=self.ids.language_parent

        if language_options.opacity==0:
            language_options.opacity=1
            language_options.disabled=False
            language_options.height="50dp"

            self.ids.arrow_icon.icon="chevron-down"
        else:
            language_options.opacity=0
            language_options.disabled=True
            language_options.height=0

            self.ids.arrow_icon.icon="chevron-right"

    # def on_pre_enter(self, *args):
    #     self.load_settings()
    # def on_kv_post(self, base_widget):
    #     super().on_kv_post(base_widget)
    #     self.ids.font_slider.bind(
    #         value=self.update_font_preview
    #     )
    #
    # def update_font_preview(self,slider,value):
    #     value=int(value)
    #     self.ids.preview_text.font_size=value
    #     self.ids.font_label.text=f"{value} px"
    #     print("slider value:",value)
    #     print("preview font size:", self.ids.preview_text.font_size)

    def select_language(self,language):
        print("Selected language:", language)
        parent=self.ids.language_parent

        # Update the label text if you want
        self.ids.language_label.text=language
        if self.ids.language_label.text=="English":
            self.ids.english_button.style="filled"
            # self.ids.english_button.md_bg_color = (0.4196, 0.2902, 0.6510, 1.0)
            # self.ids.english_text.color= (1,1,1,1)
        else:
            self.ids.english_button.style="text"
            # self.ids.english_button.md_bg_color = (0,0,0,1)
            # self.ids.english_text.color = (1, 1, 1, 1)

        if self.ids.language_label.text=="Hindi":
            self.ids.hindi_button.style="filled"
        else:
            self.ids.hindi_button.style="text"
        if self.ids.language_label.text=="French":
            self.ids.french_button.style="filled"
        else:
            self.ids.french_button.style="text"
        if self.ids.language_label.text=="Chinese":
            self.ids.chinese_button.style="filled"
        else:
            self.ids.chinese_button.style="text"

        # Hide language options
        self.ids.language_options.opacity = 0
        self.ids.language_options.disabled = True
        self.ids.arrow_icon.icon="chevron-right"
        self.ids.language_options.height= "0dp"


    def refresh_language(self):
        t = App.get_running_app().language.translate
        # self.ids.accent.text=t("Accent Color")
        if self.ids.language_label.text=="Hindi":
            self.ids.language_label.text=t("Hindi")
        else:
            self.ids.language_label.text=t("English")
        self.ids.font_size.text=t("Font Size")
        if self.ids.font_slider.value==range(11,22):
            self.ids.font_label.text=t(self.ids.font_slider.value)
        self.ids.save.text=t("Save Settings")
        self.ids.restore.text=t("Restore Default")
        self.ids.personalize.text=t("Personalize")

    def background_theme(self,selected_theme):
        self.selected_theme=selected_theme
        active=True
        dawn=self.ids.dawn
        midnight=self.ids.midnight
        login=self.manager.get_screen("login")
        signup=self.manager.get_screen("signup")
        welcome=self.manager.get_screen("welcome")
        addwish=self.manager.get_screen("add_wish")
        home=self.manager.get_screen("home")
        forgotpassword=self.manager.get_screen("forgot")
        editprofile=self.manager.get_screen("edit_profile")
        personalize=self.manager.get_screen("personalize")
        setting=self.manager.get_screen("setting")


        if selected_theme=="midnight":

            login.ids.image.source="image/midnight.png"
            login.ids.login_email.foreground_color=(1,1,1,1)
            login.ids.login_password.foreground_color=(1,1,1,1)

            signup.ids.image.source="image/midnight.png"
            signup.ids.signup_name.foreground_color=(1,1,1,1)
            signup.ids.signup_email.foreground_color=(1,1,1,1)
            signup.ids.signup_password.foreground_color=(1,1,1,1)
            signup.ids.signup_name.foreground_color=(1,1,1,1)
            signup.ids.signup_phone.foreground_color=(1,1,1,1)

            addwish.ids.image.source="image/midnight.png"
            addwish.ids.wish_name.foreground_color=(1,1,1,1)
            addwish.ids.wish_phone.foreground_color=(1,1,1,1)
            addwish.ids.wish_email.foreground_color=(1,1,1,1)
            addwish.ids.wish_subject.foreground_color=(1,1,1,1)
            addwish.ids.wish_message.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_date.foreground_color=(1,1,1,1)
            addwish.ids.wish_time.foreground_color=(1,1,1,1)
            addwish.side_panel_color = (0.0588, 0.0627, 0.1411, 1.0)
            addwish.ids.add_image.color=(1,1,1,1)

            home.ids.image.source="image/midnight.png"
            home.ids.total.color=(1,1,1,1)
            home.ids.wish_number.color=(1,1,1,1)
            home.ids.pending.color=(1,1,1,1)
            home.ids.pending_number.color=(1,1,1,1)
            home.ids.sent.color=(1,1,1,1)
            home.ids.sent_number.color=(1,1,1,1)
            home.ids.failed.color=(1,1,1,1)
            home.ids.failed_number.color=(1,1,1,1)
            home.side_panel_color = (0.0588, 0.0627, 0.1411, 1.0)
            home.ids.add_image.color=(1,1,1,1)

            forgotpassword.ids.image.source="image/midnight.png"
            forgotpassword.ids.fp_email.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.otp_input.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.new_password.foreground_color = (1, 1, 1, 1)

            welcome.ids.image.source="image/midnight.png"

            editprofile.ids.image.source="image/midnight.png"
            editprofile.ids.full_name.foreground_color = (1, 1, 1, 1)
            editprofile.ids.email.foreground_color = (1, 1, 1, 1)
            editprofile.ids.phone.foreground_color = (1, 1, 1, 1)

            personalize.ids.image.source="image/midnight.png"
            personalize.ids.theme_text.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.dark_label.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.language_text.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.font_size.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.palette_color.icon_color = (0.910, 0.831, 0.969, 1.0)
            personalize.ids.dark_icon.icon_color= (0.910, 0.831, 0.969, 1.0)
            personalize.ids.translate_icon.icon_color= (0.910, 0.831, 0.969, 1.0)
            personalize.ids.font_icon.icon_color = (0.910, 0.831, 0.969, 1.0)
            personalize.ids.language_change.md_bg_color = 1, 1, 1, 0.10
            personalize.ids.change_text.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.arrow_icon.icon_color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.preview_text.color = (0.957, 0.925, 1.0, 1.0)
            personalize.ids.preview_label.color = (0.725, 0.651, 0.831, 1.0)
            personalize.ids.sub_labels.color = (0.643, 0.576, 0.761, 1.0)
            personalize.ids.sub_labels.text = "On -- midnight glass interface"
            personalize.ids.theme_sub_label.color = (0.643, 0.576, 0.761, 1.0)
            personalize.ids.language_label.color = (0.643, 0.576, 0.761, 1.0)
            personalize.ids.font_label.color = (0.643, 0.576, 0.761, 1.0)
            personalize.ids.midnight.md_bg_color = (1, 1, 1, 0.05)
            personalize.ids.midnight_text.color = (1, 1, 1, 1)
            personalize.ids.midnight_check.icon_color = (1, 1, 1, 1)
            personalize.ids.dawn.md_bg_color = (1, 1, 1, 0.05)
            personalize.ids.dawn_text.color = (1, 1, 1, 1)
            personalize.ids.english_text.color= (1,1,1,1)
            personalize.ids.hindi_text.color= (1,1,1,1)
            personalize.ids.french_text.color= (1,1,1,1)
            personalize.ids.chinese_text.color= (1,1,1,1)

            self.outer_container_color= (
                0.0588, 0.0627, 0.1412, 1.0
            )
            self.content_container_color = (
                0.0588, 0.0627, 0.1412, 1.0
            )
            self.palette_container_color= (
                1,1,1,.10
            )
            self.track_container_color= (
                0.541, 0.420, 0.769, 1.0
            )
            self.line_container_color= (
                1,1,1,.10
            )


            setting.ids.image.source="image/midnight.png"



        elif selected_theme=="dawn":
            login.ids.image.source = "image/wisher-app-background_login.jpg"
            login.ids.login_email.foreground_color = (0, 0, 0, 1)
            login.ids.login_password.foreground_color = (0, 0, 0, 1)

            signup.ids.image.source = "image/wisher-app-background_login.jpg"
            signup.ids.signup_name.foreground_color = (0, 0, 0, 1)
            signup.ids.signup_email.foreground_color = (0, 0, 0, 1)
            signup.ids.signup_password.foreground_color = (0, 0, 0, 1)
            signup.ids.signup_phone.foreground_color = (0, 0, 0, 1)

            addwish.ids.image.source = "image/wisher-app-background_login.jpg"
            addwish.ids.wish_name.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_phone.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_email.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_subject.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_message.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_date.foreground_color = (0, 0, 0, 1)
            addwish.ids.wish_time.foreground_color = (0, 0, 0, 1)
            addwish.side_panel_color = (0.176, 0.106, 0.306, 1.0)
            addwish.ids.add_image.color = (0.7, 0.5, 0.9, 1)


            home.ids.image.source = "image/wisher-app-background_login.jpg"
            home.ids.total.color = (0, 0, 0, 1)
            home.ids.wish_number.color = (0, 0, 0, 1)
            home.ids.pending.color = (0, 0, 0, 1)
            home.ids.pending_number.color = (0, 0, 0, 1)
            home.ids.sent.color = (0, 0, 0, 1)
            home.ids.sent_number.color = (0, 0, 0, 1)
            home.ids.failed.color = (0, 0, 0, 1)
            home.ids.failed_number.color = (0, 0, 0, 1)
            home.side_panel_color = (0.176, 0.106, 0.306, 1.0)
            home.ids.add_image.color = (0.7, 0.5, 0.9, 1)

            forgotpassword.ids.image.source = "image/wisher-app-background_login.jpg"
            forgotpassword.ids.fp_email.foreground_color = (0, 0, 0, 1)
            forgotpassword.ids.otp_input.foreground_color = (0, 0, 0, 1)
            forgotpassword.ids.new_password.foreground_color = (0, 0, 0, 1)

            welcome.ids.image.source = "image/wisher-app-background_login.jpg"

            editprofile.ids.image.source = "image/wisher-app-background_login.jpg"
            editprofile.ids.full_name.foreground_color = (0, 0, 0, 1)
            editprofile.ids.email.foreground_color = (0, 0, 0, 1)
            editprofile.ids.phone.foreground_color = (0, 0, 0, 1)

            personalize.ids.image.source = "image/wisher-app-background_login.jpg"
            personalize.ids.theme_text.color = (0, 0, 0, 1)
            personalize.ids.dark_label.color = (0, 0, 0, 1)
            personalize.ids.language_text.color = (0, 0, 0, 1)
            personalize.ids.font_size.color = (0, 0, 0, 1)
            personalize.ids.palette_color.icon_color = (0,0,0,1)
            personalize.ids.dark_icon.icon_color=(0,0,0,1)
            personalize.ids.translate_icon.icon_color = (0, 0, 0, 1)
            personalize.ids.font_icon.icon_color = (0, 0, 0, 1)
            personalize.ids.language_change.md_bg_color = (1, 1, 1, 1)
            personalize.ids.change_text.color = (0,0,0,1)
            personalize.ids.arrow_icon.icon_color = (0,0,0,1)
            personalize.ids.preview_text.color = (0,0,0,1)
            personalize.ids.preview_label.color = (0.3, 0.3, 0.3, 1)
            personalize.ids.sub_labels.color = (0.3, 0.3, 0.3, 1)
            personalize.ids.sub_labels.text = "Off -- bright, daytime interface"
            personalize.ids.theme_sub_label.color = (0.3, 0.3, 0.3, 1)
            personalize.ids.language_label.color = (0.3, 0.3, 0.3, 1)
            personalize.ids.font_label.color = (0.3, 0.3, 0.3, 1)
            personalize.ids.midnight_text.color = (0, 0, 0, 1)
            personalize.ids.midnight_check.icon_color = (0, 0, 0, 1)
            personalize.ids.dawn_text.color = (0,0,0, 1)
            personalize.ids.dawn_check.icon_color = (0, 0, 0, 1)
            personalize.ids.dawn.md_bg_color = (1, 1, 1, 1)
            personalize.ids.dawn.line_color = (0, 0, 0, 1)
            personalize.ids.english_text.color = (0, 0, 0, 1)
            personalize.ids.hindi_text.color = (0, 0, 0, 1)
            personalize.ids.french_text.color = (0, 0, 0, 1)
            personalize.ids.chinese_text.color = (0, 0, 0, 1)


            self.outer_container_color = (
                1,1,1,.15
            )
            self.content_container_color=(
                0.91, 0.831, 0.969, 1.0
            )
            self.palette_container_color=(
                1,1,1,1
            )
            self.track_container_color= (
                0,0,0,1
            )
            self.line_container_color= (
                1,1,1,1
            )

            setting.ids.image.source="image/wisher-app-background_login.jpg"

    def dark_mode(self):
        login = self.manager.get_screen("login")
        signup = self.manager.get_screen("signup")
        welcome = self.manager.get_screen("welcome")
        addwish = self.manager.get_screen("add_wish")
        home = self.manager.get_screen("home")
        forgotpassword = self.manager.get_screen("forgot")
        editprofile = self.manager.get_screen("edit_profile")
        personalize = self.manager.get_screen("personalize")
        setting = self.manager.get_screen("setting")
        dark_mode = self.ids.dark_switch

        if dark_mode.active==True:
            login.ids.image.source = "image/wisher-background-darkmode.jpg"
            login.ids.login_email.foreground_color = (1, 1, 1, 1)
            login.ids.login_password.foreground_color = (1, 1, 1, 1)

            signup.ids.image.source = "image/wisher-background-darkmode.jpg"
            signup.ids.signup_name.foreground_color = (1, 1, 1, 1)
            signup.ids.signup_email.foreground_color = (1, 1, 1, 1)
            signup.ids.signup_password.foreground_color = (1, 1, 1, 1)
            signup.ids.signup_name.foreground_color = (1, 1, 1, 1)
            signup.ids.signup_phone.foreground_color = (1, 1, 1, 1)

            addwish.ids.image.source = "image/wisher-background-darkmode.jpg"
            addwish.ids.wish_name.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_phone.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_email.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_subject.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_message.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_date.foreground_color = (1, 1, 1, 1)
            addwish.ids.wish_time.foreground_color = (1, 1, 1, 1)
            addwish.side_panel_color = (0.0588, 0.0627, 0.1411, 1.0)
            addwish.ids.add_image.color = (1, 1, 1, 1)

            home.ids.image.source = "image/wisher-background-darkmode.jpg"
            home.ids.total.color = (1, 1, 1, 1)
            home.ids.wish_number.color = (1, 1, 1, 1)
            home.ids.pending.color = (1, 1, 1, 1)
            home.ids.pending_number.color = (1, 1, 1, 1)
            home.ids.sent.color = (1, 1, 1, 1)
            home.ids.sent_number.color = (1, 1, 1, 1)
            home.ids.failed.color = (1, 1, 1, 1)
            home.ids.failed_number.color = (1, 1, 1, 1)
            home.side_panel_color = (0.0588, 0.0627, 0.1411, 1.0)
            home.ids.add_image.color = (1, 1, 1, 1)

            forgotpassword.ids.image.source = "image/wisher-background-darkmode.jpg"
            forgotpassword.ids.fp_email.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.otp_input.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.new_password.foreground_color = (1, 1, 1, 1)

            welcome.ids.image.source = "image/wisher-background-darkmode.jpg"

            editprofile.ids.image.source = "image/wisher-background-darkmode.jpg"
            editprofile.ids.full_name.foreground_color = (1, 1, 1, 1)
            editprofile.ids.email.foreground_color = (1, 1, 1, 1)
            editprofile.ids.phone.foreground_color = (1, 1, 1, 1)

            personalize.ids.image.source = "image/wisher-background-darkmode.jpg"
            # personalize.ids.image.background_color= (0.0784, 0.0392, 0.1529, 1.0)
            personalize.ids.theme_text.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.dark_label.color= (0.949, 0.914, 1.0, 1.0)
            personalize.ids.language_text.color = (0.949, 0.914, 1.0, 1.0)
            personalize.ids.font_size.color= (0.949, 0.914, 1.0, 1.0)
            personalize.ids.palette_color.icon_color= (0.910, 0.831, 0.969, 1.0)
            personalize.ids.dark_icon.icon_color = (0.910, 0.831, 0.969, 1.0)
            personalize.ids.translate_icon.icon_color = (0.910, 0.831, 0.969, 1.0)
            personalize.ids.font_icon.icon_color = (0.910, 0.831, 0.969, 1.0)
            personalize.ids.language_change.md_bg_color= 1,1,1,0.10
            personalize.ids.change_text.color= (0.949, 0.914, 1.0, 1.0)
            personalize.ids.arrow_icon.icon_color= (0.949, 0.914, 1.0, 1.0)
            personalize.ids.preview_text.color = (0.957, 0.925, 1.0, 1.0)
            personalize.ids.preview_label.color= (0.725, 0.651, 0.831, 1.0)
            personalize.ids.sub_labels.color= (0.643, 0.576, 0.761, 1.0)
            personalize.ids.sub_labels.text="On -- midnight glass interface"
            personalize.ids.theme_sub_label.color= (0.643, 0.576, 0.761, 1.0)
            personalize.ids.language_label.color= (0.643, 0.576, 0.761, 1.0)
            personalize.ids.font_label.color= (0.643, 0.576, 0.761, 1.0)
            personalize.ids.midnight.md_bg_color= (1,1,1,0.05)
            if self.selected_theme=="midnight":
                personalize.ids.midnight.line_color = (0.541, 0.420, 0.769, 1.0)
            personalize.ids.dawn.md_bg_color = (1, 1, 1, 0.05)
            if self.selected_theme=="dawn":
                personalize.ids.dawn.line_color = (0.541, 0.420, 0.769, 1.0)
            personalize.ids.midnight_text.color= (1,1,1,1)
            personalize.ids.midnight_check.icon_color= (1,1,1,1)
            personalize.ids.dawn_text.color = (1, 1, 1, 1)
            personalize.ids.dawn_check.icon_color = (1, 1, 1, 1)


            self.outer_container_color = (
                0.1, 0.04, 0.18, 0.35
            )
            self.content_container_color = (
                0.1, 0.04, 0.18, 0.55
            )
            self.palette_container_color=(
                1,1,1,.10
            )
            self.track_container_color= (
                0.541, 0.420, 0.769, 1.0
            )
            self.line_container_color= (
                1,1,1,0.10
            )

            setting.ids.image.source = "image/wisher-background-darkmode.jpg"
        elif dark_mode.active==False:
            if self.selected_theme=="dawn":
                self.background_theme("dawn")

            elif self.selected_theme =="midnight":
                self.background_theme("midnight")

    def restore_default(self):
        self.ids.theme.text = self.background_theme("dawn")
        self.ids.language_label.text = "English"
        self.ids.font_slider.value = 16

    def save_settings(self):
        # if self.selected_theme=="midnight":
        #     self.selected_theme= "midnight"
        # elif self.selected_theme=="dawn":
        #     self.selected_theme = "dawn"
        theme=self.selected_theme

        language = self.ids.language_label.text
        font_size = self.ids.font_label.text
        conn9 = sqlite3.connect("user.db")
        cursor9 = conn9.cursor()

        cursor9.execute("""
        INSERT OR REPLACE INTO personalize
        (user_id,theme,language,font_size)
        VALUES(?,?,?,?)
        """,(
                           current_user["id"],
                           theme,
                           language,
                           font_size
                       ))

        conn9.commit()
        conn9.close()
        App.get_running_app().language.current_language = language
        self.manager.current = "home"

        print(theme)
        print(language)
        print(font_size)

    def load_settings(self):
        print("current_user:", current_user["id"])
        conn21=sqlite3.connect("user.db")
        cursor21=conn21.cursor()

        cursor21.execute("SELECT * FROM personalize WHERE user_id=?",(current_user["id"],))
        row=cursor21.fetchone()
        conn21.close()

        if row is not None:
            self.selected_theme = row[1]
            self.background_theme(str(self.selected_theme))
            self.ids.language_label.text = row[2]
            self.ids.font_label.text = row[3]

            print("Theme:", self.selected_theme)
            print("Language:", row[2])
            print("Font size:", row[3])

        else:
            # No settings saved for this user
            self.selected_theme = "dawn"
            self.ids.language_label.text = "English"
            self.ids.font_label.text = "18"

            self.background_theme("dawn")

            print("No personalization settings found.")



class HistoryScreen(Screen):


    def on_pre_enter(self, *args):
        self.load_history()

    def load_history(self):
        self.ids.history_container.clear_widgets()
        conn10 = sqlite3.connect("user.db")
        cursor10 = conn10.cursor()

        cursor10.execute("""
            SELECT
                name,
                phone,
                recipient_email,
                subject,
                date,
                time,
                sent,
                platform
            FROM wishes WHERE user_id=?
            ORDER BY date DESC,time DESC
            """, (current_user["id"],))
        rows = cursor10.fetchall()
        conn10.close()

        for row in rows:
            # contact=""
            if row[7] == "Email":
                contact=row[2] or ""
            else:
                contact=row[1] or ""

            card=HistoryCard(
                name=str(row[0] or ""),
                platform=str(row[7] or ""),
                contact=str(contact or ""),
                subject=str(row[3] or ""),
                date=str(row[4] or ""),
                time=str(row[5] or ""),
                status="Sent" if row[6] == 1 else "Failed"
            )
            self.ids.history_container.add_widget(card)

    def search_history(self,keyword):
        keyword=keyword.lower()
        self.ids.history_container.clear_widgets()
        conn11=sqlite3.connect("user.db")
        cursor11=conn11.cursor()
        cursor11.execute("""
            SELECT
                name,
                phone,
                recipient_email,
                subject,
                date,
                time,
                sent,
                platform
            FROM wishes
            WHERE LOWER(name) LIKE ? and user_id=?
            """, ("%"+keyword+"%", current_user["id"],))

        rows = cursor11.fetchall()
        conn11.close()
        for row in rows:
            contact=str(row[2] or "") if row[7] == "Email" else str(row[1] or "")

            self.ids.history_container.add_widget(
                HistoryCard(
                    name=str(row[0] or ""),
                    platform=str(row[7] or ""),
                    contact=str(contact or ""),
                    subject=str(row[3] or ""),
                    date=str(row[4] or ""),
                    time=str(row[5] or ""),
                    status="Sent" if row[6] == 1 else "Failed"
                )
            )


class HistoryCard(BoxLayout):
    name = StringProperty("")
    platform = StringProperty("")
    contact = StringProperty("")
    subject = StringProperty("")
    date = StringProperty("")
    time = StringProperty("")
    status = StringProperty("")


class SettingScreen(Screen):

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.current_tab = None
        self.general_content = GeneralContent()
        self.advanced_content=AdvancedContent()
        self.notification_content = NotificationContent()
    def on_enter(self, *args):
        self.show_general()

    def show_notification(self):
        self.ids.content_area.clear_widgets()
        self.notification_content.load_ntf_settings()
        self.ids.content_area.add_widget(self.notification_content)
        # self.ids.save_btn.opacity = 1
        # self.ids.save_btn.disabled = False
        #
        # self.current_tab = "notification"

    def show_storage(self):
        self.ids.content_area.clear_widgets()
        self.ids.content_area.add_widget(
            StorageContent()
        )

    def show_general(self):
        self.ids.content_area.clear_widgets()
        self.general_content.load_general_settings()
        self.ids.content_area.add_widget(
            self.general_content
        )
        # self.ids.save_btn.opacity = 1
        # self.ids.save_btn.disabled = False
        #
        # self.current_tab = "general"

    def show_about(self):
        self.ids.content_area.clear_widgets()
        self.ids.content_area.add_widget(
            AboutContent()
        )

    def show_advanced(self):
        self.ids.content_area.clear_widgets()
        self.advanced_content.load_adv_settings()
        self.ids.content_area.add_widget(
            self.advanced_content
        )
        # self.ids.save_btn.opacity = 1
        # self.ids.save_btn.disabled = False
        #
        # self.current_tab = "advanced"

    def save_current_settings(self):

        if self.current_tab == "general":
            self.general_content.save_general_settings()

        elif self.current_tab == "notification":
            self.notification_content.save_notification_settings()

        elif self.current_tab == "appearance":
            self.personalize_content.save_settings()

        elif self.current_tab == "advanced":
            self.advanced_content.save_adv_settings()

class NotificationContent(BoxLayout):
    
    def save_ntf_settings(self):

        notification_switch=int(self.ids.notification_switch.active)
        sound_switch=int(self.ids.sound_switch.active)
        reminder=self.ids.reminder.text
        conn18=sqlite3.connect("user.db")
        cursor18=conn18.cursor()

        cursor18.execute("""
        INSERT OR REPLACE INTO notification_settings(
        id,
        enable_notification,
        sound,
        reminder
        ) VALUES(1,?,?,?)""",(notification_switch,sound_switch,reminder))

        conn18.commit()


        conn18.close()


    def load_ntf_settings(self):
        conn19=sqlite3.connect("user.db")
        cursor19=conn19.cursor()

        cursor19.execute("""SELECT * FROM notification_settings WHERE id=1""")

        row=cursor19.fetchone()
        if row:
            self.ids.notification_switch.active=row[1]
            self.ids.sound_switch.active=row[2]
            self.ids.reminder.text=row[3]

        conn19.close()
        print("Notification settings loaded:",row)



def play_notification_sound():
    notification_sound=SoundLoader.load("audio/alert.wav")
    if notification_sound:
        notification_sound.play()

def send_notification(title, message,enable_notification,sound):
    app_icon="image/wisher-brand-logo.ico"
    if not enable_notification:
        return

    notification.notify(
        title=title,
        message=message,
        app_name="Wisher",
        app_icon=app_icon,
        timeout=10
    )

    # Play Windows notification sound
    if sound:
        play_notification_sound()



class StorageContent(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cache_folder = None

    def clear_cache(self):
        self.cache_folder = "__pycache__"

        if os.path.exists(self.cache_folder):
            shutil.rmtree(self.cache_folder)

        print("Cache Cleared")

    @staticmethod
    def clear_history():

        conn10 = sqlite3.connect("user.db")
        cursor10 = conn10.cursor()

        cursor10.execute("""
            DELETE FROM wishes
            WHERE sent=1
        """)

        conn10.commit()
        conn10.close()

        print("History Cleared")

    @staticmethod
    def delete_failed():

        conn11 = sqlite3.connect("user.db")
        cursor11 = conn11.cursor()

        cursor11.execute("""
            DELETE FROM wishes
            WHERE sent=0
        """)

        conn11.commit()
        conn11.close()

        print("Failed Wishes Deleted")

    @staticmethod
    def delete_all():

        conn12 = sqlite3.connect("user.db")
        cursor12 = conn12.cursor()

        cursor12.execute("DELETE FROM wishes")

        conn12.commit()
        conn12.close()

        print("All Wishes Deleted")

class GeneralContent(BoxLayout):

    # @staticmethod
    # def mark_dirty():
    #     settings = App.get_running_app().root.get_screen("setting")
    #     settings.ids.save_btn.opacity = 1
    #     settings.ids.save_btn.disabled = False

    def save_general_settings(self):
        conn14=sqlite3.connect("user.db")
        cursor14=conn14.cursor()
        launch = int(self.ids.startup_switch.active)
        tray = int(self.ids.tray_switch.active)
        auto_scheduler = int(self.ids.scheduler_switch.active)

        time_format = self.ids.time_spinner.text
        date_format = self.ids.date_spinner.text
        timezone = self.ids.timezone_spinner.text

        cursor14.execute("""
            INSERT OR REPLACE INTO general_settings(
                id,
                launch_startup,
                minimize_tray,
                auto_scheduler,
                time_format,
                date_format,
                time_zone
            )
            VALUES(1,?,?,?,?,?,?)
            """, (
            launch,
            tray,
            auto_scheduler,
            time_format,
            date_format,
            timezone
        ))

        conn14.commit()
        conn14.close()

        print("General settings saved.")



    def load_general_settings(self):
        conn15 = sqlite3.connect("user.db")
        cursor15 = conn15.cursor()

        cursor15.execute("""
        SELECT * FROM general_settings WHERE id=1
        """)

        row = cursor15.fetchone()

        print("General settings loaded:",row)

        if row:
            self.ids.startup_switch.active =row[1]
            self.ids.tray_switch.active = row[2]
            self.ids.scheduler_switch.active = int(row[3])

            self.ids.time_spinner.text = row[4]
            self.ids.date_spinner.text = row[5]
            self.ids.timezone_spinner.text = row[6]

        conn15.close()

    def on_startup_switch(self,switch,value):
        self.ids.startup_switch.active = value
        if value == 1:
            enable_startup()
        else:
            disable_startup()

APP_NAME = "Wisher App"

def enable_startup():
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE
    )

    winreg.SetValueEx(
        key,
        APP_NAME,
        0,
        winreg.REG_SZ,
        f'"{sys.executable}"'
    )

    winreg.CloseKey(key)

def disable_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )

        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)

    except FileNotFoundError:
        pass

def startup_enabled():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run"
        )

        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True

    except FileNotFoundError:
        return False

class AboutContent(BoxLayout):

    @staticmethod
    def rate_app():
        print("Rate App Clicked")

    @staticmethod
    def share_app():
        print("Share App Clicked")

scheduler_thread= threading.Thread(target=scheduler.run)
notification_thread= threading.Thread(target=notification.notify)
class AdvancedContent(BoxLayout):

    def save_adv_settings(self):
        conn12 = sqlite3.connect("user.db")
        cursor12 = conn12.cursor()
        interval = self.ids.interval_spinner.text
        cursor12.execute("""INSERT OR REPLACE INTO advanced_settings(
                                    id,
                                    scheduler_status,
                                    scheduler_interval) VALUES(1,?,?) """, (self.ids.scheduler_status.text,interval,))
        conn12.commit()
        conn12.close()

    def load_adv_settings(self):
        conn13=sqlite3.connect("user.db")
        cursor13=conn13.cursor()
        cursor13.execute("""SELECT * FROM advanced_settings WHERE id=1""")

        row=cursor13.fetchone()

        if row:
            self.ids.scheduler_status.text=row[1]
            self.ids.interval_spinner.text=row[2]

        conn13.close()

    def start_scheduler(self):

        global scheduler_thread
        global notification_thread

        scheduler_status=self.ids.scheduler_status
        if scheduler_thread is None or not scheduler_thread.is_alive():
            scheduler_stop_event.clear()
            scheduler_thread = threading.Thread(target=run_scheduler,daemon=True).start()
            print("Scheduler Started")
            scheduler_status.text="Running"

        if notification_thread is None or not notification_thread.is_alive():
            notification_thread = threading.Thread(
                target=notification_scheduler,
                daemon=True
            )
            notification_thread.start()




    def stop_scheduler(self):

        scheduler_stop_event.set()
        print("Scheduler Stopped")
        self.ids.scheduler_status.text="stopped"


    def restart_scheduler(self):
        self.stop_scheduler()
        time.sleep(1)
        self.start_scheduler()
        print("Scheduler Restarted")
        self.ids.scheduler_status.text="Running"


class DashboardScreen(WelcomeScreen):
    pass
#===============Screen Manager================
class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(
            transition=WipeTransition(),
            **kwargs
        )




def close_whatsapp(wish):
    time.sleep(10)
    plat_form=wish[8]
    if "WhatsApp" in plat_form :
        try:
            subprocess.run(
                ["taskkill","/F","/IM","WhatsApp.Root.exe"],
                capture_output=True,
                text=True
            )
            print("WhatsApp closed")
        except Exception as e:
            print("Error closing WhatsApp:",e)

def save_credentials(user_email):
    conn5 = sqlite3.connect("user.db")
    cursor5 = conn5.cursor()
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes
        )
        creds = flow.run_local_server(port=0,open_browser=True,timeout_seconds=120)
        if not creds:
            print("Gmail authorization cancelled.")
            return False
        cursor5.execute("""INSERT OR REPLACE INTO gmail_tokens(
                            user_email,
                            token,
                            refresh_token,
                            token_uri,
                            client_id,
                            client_secret,
                            scopes,
                            expiry
                        )
                        VALUES(?,?,?,?,?,?,?,?)""",
                        (
                            user_email,
                            creds.token,
                            creds.refresh_token,
                            creds.token_uri,
                            creds.client_id,
                            creds.client_secret,
                            ",".join(creds.scopes),
                            creds.expiry.isoformat()
                        )
                        )
        conn5.commit()
        print("Gmail credentials saved.")
        return True

    except Exception as e:
        print("Gmail authorization failed or cancelled:",repr(e))
        return False

    finally:
        conn5.close()


scopes=["https://www.googleapis.com/auth/gmail.send"]

def send_message(wish):
    load_dotenv()
    name = wish[2]
    recipient_phone = wish[3]
    recipient_email=wish[4]
    message = wish[5]
    subject = wish[6]
    plat_form=wish[9].split(",")
    phone_number_id=os.getenv("PHONE_NUMBER_ID")

    conn5=sqlite3.connect("user.db")
    cursor5=conn5.cursor()
    whatsapp_url = (f"https://graph.facebook.com/v26.0/"
                    f"{phone_number_id}/messages"
                    )
    access_token="EAATHaYVxEz0BSXmaHcgg9PPjfi7fuLvQ3pVwwtGAeoPluwYiQtZBJhLQtKKLzEawWMk7qFZCY2IQOxdyKJTqZBiYPeaWj5HI1cXGii4aiBN5mpEEo32viELUVuciNU5lPDZAtH3eR5TZBCltAFtntHfBCah7XtTetl49PIcrt0ZA8wYxszB8E2u28ZAh5mu50fIyi7on1a8T968rpH5PXbLcFjdzTEo7ZBkMAotc"

    def generate_appsecret_proof(access_token, app_secret):
        app_secret=os.getenv("APP_SECRET")
        access_token=os.getenv("ACCESS_TOKEN")
        return hmac.new(
            app_secret.encode("utf-8"),
            access_token.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    if "WhatsApp" in plat_form:
        try:
            # appsecret_proof = generate_appsecret_proof(
            #     os.getenv("ACCESS_TOKEN"),
            #     os.getenv("APP_SECRET")
            # )
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient_phone,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            # params = {
            #     "appsecret_proof": appsecret_proof
            # }

            response=requests.post(whatsapp_url,headers=headers,json=data,timeout=50)
            print(response.status_code)
            print(response.text)
            return response.ok


            # print(f"Opening WhatsApp for {name}")
            # # Trigger Windows to open the URI with the WhatsApp desktop application
            # subprocess.Popen(["cmd", "/C", f"start {whatsapp_uri}"], shell=True)
            # # Wait for the desktop application to open and load the chat window
            # time.sleep(10)
            # # it touches the chat window
            # pyautogui.click()
            # # Type the message automatically
            # pyautogui.typewrite(f"{message}")
            #
            # time.sleep(1)
            # # Press enter to send the message
            # pyautogui.press('enter')

        except Exception as e:
            print(e)

    if "Email" in plat_form:
        try:
            senders_email=current_user["email"]

            cursor5.execute("""
                SELECT
                token,
                refresh_token,
                token_uri,
                client_id,
                client_secret,
                scopes
                FROM gmail_tokens
                WHERE user_email=?
                """, (senders_email,))

            row = cursor5.fetchone()
            if row is None:
                show_popup(title="",message="No Gmail account connected")
                conn5.close()
                return

            creds = Credentials(
                token=row[0],
                refresh_token=row[1],
                token_uri=row[2],
                client_id=row[3],
                client_secret=row[4],
                scopes=row[5].split(",")
            )
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())

                cursor5.execute("""
                UPDATE gmail_tokens
                SET token=?,
                    expiry=?
                WHERE user_email=?
                """,
                (
                    creds.token,
                    creds.expiry.isoformat(),
                    senders_email
                ))

                conn5.commit()
            service=build(
                "Gmail",
                "v1",
                credentials=creds,
            )
            msg=MIMEText(message)
            msg["to"]=recipient_email
            msg["subject"]=subject
            raw=base64.urlsafe_b64encode(msg.as_bytes()).decode()

            service.users().messages().send(
                userId="me",
                body={
                    "raw":raw
                }
            ).execute()

        except Exception as e:
            print(e)

    if "SMS" in plat_form:
        pass


def scheduler_interval():
    setting = App.get_running_app().root.get_screen("setting")
    advanced = setting.advanced_content
    interval = advanced.ids.interval_spinner.text
    mapping = {
        "10 seconds": 10,
        "20 seconds": 20,
        "30 seconds": 30,
        "1 minute": 60,
    }
    return mapping.get(interval,20)

def check_wishes():
    interval=scheduler_interval()
    conn1=sqlite3.connect("user.db")
    cursor1=conn1.cursor()
    cursor1.execute("""SELECT * FROM wishes WHERE sent=0                                 
                    """)
    all_wishes = cursor1.fetchall()

    now = datetime.now()

    cursor1.execute("SELECT enable_notification,sound,reminder FROM notification_settings WHERE id=1")
    row=cursor1.fetchone()
    if row:
        enable_notification=row[0]
        sound=row[1]
    else:
        enable_notification=True
        sound=True
    for wish in all_wishes:
        wish_id = wish[0]
        name = wish[2]
        date = wish[7]
        time_str = wish[8]
        plat_form=wish[9].split(",")



        try:
            # Combine date + time
            wish_time = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M:%S %p")


        except ValueError:
            print(f"Invalid date/time format {date} {time_str}")
            conn1.commit()
            continue

        # ---------------- Pending ----------------
        if wish_time > now:
            cursor1.execute("""UPDATE wishes SET status="Pending" WHERE id=?""", (wish_id,))
            conn1.commit()
            continue

        # ---------------- Send Wish ----------------
        if wish_time <= now <= wish_time + timedelta(seconds=interval):

            try:
                print(f"Sending wish to {name}")
                send_message(wish)
                # ✅ MARK SENT FIRST
                cursor1.execute(
                    """UPDATE wishes SET sent=1,status="Success" WHERE id=?""",
                    (wish_id,)
                )

                conn1.commit()
                send_notification(
                    enable_notification=enable_notification,
                    sound=sound,
                    title="Wish Sent",
                   message= f"{name}'s wish was sent successfully."
                )

                if "WhatsApp" in plat_form:
                    # Exit WhatsApp after 10 seconds
                    threading.Thread(target=close_whatsapp,args=(wish,), daemon=True).start()

            except Exception as e:
                print(e)

                cursor1.execute("""UPDATE wishes SET status="Failed" WHERE id=?""",(wish_id,))
                conn1.commit()

        elif now>wish_time+timedelta(seconds=interval):
            cursor1.execute("""UPDATE wishes SET status="Failed" WHERE id=?""",(wish_id,))
            conn1.commit()
            # send_notification(
            #     enable_notification=enable_notification,
            #     sound=sound,
            #     title="Wish failed",
            #     message=f"{name}'s wish was failed"
            # )
    conn1.close()


def check_notifications():

    conn21 = sqlite3.connect("user.db")
    cursor21 = conn21.cursor()



    # Read notification settings once
    cursor21.execute("""
        SELECT enable_notification,
               sound,
               reminder
        FROM notification_settings
        WHERE id=1
    """)

    row = cursor21.fetchone()

    if row:
        enable_notification = bool(row[0])
        sound = bool(row[1])
        reminder = row[2]
    else:
        enable_notification = True
        sound = True
        reminder = "5 minutes"

    reminder_map = {
        "5 minutes": 5,
        "10 minutes": 10,
        "15 minutes": 15,
        "30 minutes": 30,
        "1 hour": 60
    }

    reminder_minutes = reminder_map.get(reminder.lower(), 5)
    # Read only pending wishes
    cursor21.execute("""
           SELECT id, name, date, time, reminder_sent
           FROM wishes
           WHERE sent=0
       """)

    wishes = cursor21.fetchall()

    now = datetime.now()

    for wish in wishes:

        wish_id = wish[0]
        name = wish[1]
        wish_date = wish[2]
        wish_time_str = wish[3]
        reminder_sent = int(wish[4])

        if reminder_sent==1:
            continue
        wish_time = datetime.strptime(
            f"{wish_date} {wish_time_str}",
            "%Y-%m-%d %H:%M:%S %p"
        )

        reminder_time = wish_time - timedelta(
            minutes=reminder_minutes
        )

        if reminder_time <= now < wish_time:
            send_notification(
                enable_notification=enable_notification,
                sound=sound,
                title="Upcoming Wish",
                message=f"{name}'s wish will be sent in {reminder}."
            )

            cursor21.execute("""
                UPDATE wishes
                SET reminder_sent=1
                WHERE id=?
            """, (wish_id,))

            conn21.commit()
            continue
    conn21.close()

scheduler_stop_event=threading.Event()

def run_scheduler():

    while not scheduler_stop_event.is_set():
        try:
            check_wishes()
        except Exception as e:
            print("Scheduler Error:", e)

        time.sleep(1)  # check every 30 seconds (better accuracy)   # check every minute

def notification_scheduler():
    while not scheduler_stop_event.is_set():
        try:
            check_notifications()
        except Exception as e:
            print("Notification scheduler Error:", e)

        time.sleep(1)

def reset_scheduler_status():
    conn14=sqlite3.connect("user.db")
    cursor14=conn14.cursor()

    cursor14.execute("""UPDATE advanced_settings SET scheduler_status = 'Running' WHERE id=1""")
    conn14.commit()
    conn14.close()

#================App===============
class WisherApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tray_icon = self.icon
        self.language = language_manager

    def build(self):
        root=Builder.load_file("main.kv")
        Window.bind(on_request_close=self.on_request_close)
        self.language=language_manager
        self.language.bind(current_language=self.on_language_changed)
        return root

    def restore_login(self):
        personalize=self.root.get_screen("personalize")
        conn23 = sqlite3.connect("user.db")
        cursor23 = conn23.cursor()

        cursor23.execute("""
                SELECT user_id
                FROM login_session
                WHERE id=1 AND is_logged_in=1
            """)

        row = cursor23.fetchone()
        if row is None:
            return False

        user_id = row[0]
        print(user_id)

        # Get complete user information

        cursor23.execute("""
                SELECT id, name, email, phone
                FROM users
                WHERE id=?
            """, (user_id,))

        user = cursor23.fetchone()

        if user is None:
            return False

        # Restore current_user
        current_user["id"] = user[0]
        current_user["name"] = user[1]
        current_user["email"] = user[2]
        current_user["phone"] = user[3]

        personalize.load_settings()
        return True

    def on_request_close(self,*args):

        conn17 = sqlite3.connect("user.db")
        cursor17 = conn17.cursor()

        cursor17.execute("""
                SELECT minimize_tray
                FROM general_settings
                WHERE id=1
            """)

        row = cursor17.fetchone()
        conn17.close()

        minimize = bool(row[0]) if row else False

        if minimize:
            Window.hide()

            threading.Thread(
                target=self.create_tray_icon,
                daemon=True
            ).start()
        else:
            App.get_running_app().stop()


        return True

    def restore_window(self, _icon=None, _item=None):

        def restore(_dt):
            Window.show()

            if hasattr(self, "tray_icon"):
                self.tray_icon.stop()

        Clock.schedule_once(restore)

    def exit_app(self, _icon=None, _item=None):

        def stop(_dt):
            if hasattr(self, "tray_icon"):
                self.tray_icon.stop()

            App.get_running_app().stop()

        Clock.schedule_once(stop)

    def create_tray_icon(self):

        image = Image.open("image/wisher-brand-logo.png")  # Use your app icon

        menu = pystray.Menu(
            Item("Open", self.restore_window,default=True),
            Item("Exit", self.exit_app)
        )
        self.tray_icon = pystray.Icon(
            "Wisher",
            image,
            "Wisher",
            menu
        )

        self.tray_icon.run()

    def on_start(self):
        initialize_database()

        conn16 = sqlite3.connect("user.db")
        cursor16 = conn16.cursor()

        cursor16.execute("""
        SELECT auto_scheduler
        FROM general_settings
        WHERE id=1
        """)

        row = cursor16.fetchone()
        if row is None:
            return

        if row[0]==1:
            threading.Thread(
                target=run_scheduler, daemon=True
            ).start()
            reset_scheduler_status()
            threading.Thread(target=notification_scheduler, daemon=True).start()
        else:
            # cursor16.execute("""
            # UPDATE general_settings SET auto_scheduler = 1 WHERE id=1""")
            # conn16.commit()


            conn16.close()

        self.root.current="flash"



    def on_language_changed(self,*args):
        if not self.root:
            return
        for screen in self.root.screens:
            if hasattr(screen,"refresh_language"):
                screen.refresh_language()
if __name__ == '__main__':
    WisherApp().run()

