import base64
import os
import random
import shutil
import smtplib
from email.mime.text import MIMEText
from sched import scheduler

import pystray
from pystray import MenuItem as Item
from PIL import Image
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from kivy.animation import Animation
from kivy.app import App
# from kivy.app import App
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.metrics import sp
from kivy.properties import StringProperty, ListProperty, ColorProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
# from kivy.uix.popup import Popup
# from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.pickers import MDTimePickerDialHorizontal,MDModalDatePicker
from kivy.lang import Builder
from kivy.core.window import Window
import sqlite3
# import pywhatkit
import subprocess
import pyautogui
import time
import threading
from kivymd.app import MDApp
from datetime import datetime, timedelta
from kivy.core.text import LabelBase
from google_auth_oauthlib.flow import InstalledAppFlow
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText,MDDialogSupportingText,MDDialogButtonContainer
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.widget import MDWidget

from languages import LANGUAGES

my_email="rishabhjadonrishabh@gmail.com"
my_password="jstt sgha quei xjrk"
current_user={
    "id":None,
    "name":"",
    "email":"",
    "phone":"",
}

Window.size=(780,750)

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
conn = sqlite3.connect('user.db')
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
email TEXT UNIQUE,
phone TEXT,
password TEXT
google_password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS wishes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
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
conn.commit()

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
conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS advanced_settings(
id INTEGER PRIMARY KEY AUTOINCREMENT,
scheduler_status TEXT,
scheduler_interval TEXT
)""")
conn.commit()

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
conn.commit()

def show_popup(title, message):

    # dialog = None

    ok_button = MDButton(
        style="text",
        pos_hint={"center_x":0.5, "center_y":0.5},
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
            ok_button,
            spacing="0dp"
        ),

        md_bg_color=(1, 1, 1, 1),
    )

    ok_button.bind(
        on_release=lambda *args: dialog.dismiss()
    )

    dialog.open()

class HoverButton(Button):
    hovered=False
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self,*args):

        if not self.get_root_window():
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


class FlashScreen(Screen):
    def __init__(self,**kwargs):
        super().__init__()
        self.loading_event = None

    def on_enter(self,*args):
        self.ids.loading_bar.value = 0

        self.loading_event = Clock.schedule_interval(
            self.update_loading,
            0.05
        )

        self.animate_logo()
        self.splash_label_animate()

    def animate_logo(self):
        splash_logo = self.ids.splash_logo
        splash_logo.opacity = 0
        splash_logo.scale = 0.8
        Animation(
            opacity=1,
            duration=1,
            t="out_back"

        ).start(splash_logo)

    def splash_label_animate(self):
        splash_label=self.ids.splash_label
        splash_label.opacity=0
        splash_label.font_size=sp(30)
        Animation.cancel_all(splash_label)
        (
            Animation(
                opacity=1,
                font_size=sp(60),
                duration=1.2,
                t="out_back"
            )+
            Animation(
                duration=1,
                font_size=sp(50),
                t="in_out_quad"

            )
        ).start(splash_label)
        # Clock.schedule_once(
        # self.goto_login,
        #     5
        # )

    def update_loading(self, _dt):
        self.ids.loading_bar.value += 1

        if self.ids.loading_bar.value >= 100:
            self.loading_event.cancel()
            self.manager.current = "login"
            return False

        return True

    # def goto_login(self,_dt):
    #    self.manager.current="login"

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
        global current_user
        email=self.ids.login_email.text
        phone=self.ids.login_email.text
        password=self.ids.login_password.text
        # Empty Field Check
        if not email or not password:
            show_popup(title="required",message="Please fill all fields")
            return

        # Database Check
        cursor.execute("SELECT * FROM users WHERE email=? or phone=? or password=?",(email,phone,password))
        user = cursor.fetchone()

        # check password
        #stored_password=user[4]

        if user and password==user[4] :
            print("Login Successful")
            current_user["id"]=user[0]
            current_user["email"]=user[2]
            current_user["phone"]=user[3]
            current_user["name"]=user[1]
            self.manager.current = "welcome"
            self.ids.login_email.text = ""
            self.ids.login_password.text = ""
        if user is None:
            show_popup(title="error",message="User does not exist. Please SignUp")
            return
        if password != user[4]:
            show_popup(title="error",message="Password is Wrong")
            return


    def start_google_login(self):
        threading.Thread(
            target=self.google_signin,
            daemon=True
        ).start()

    def google_signin(self):
        # webbrowser.open(
        #     "https://accounts.google.com/signin"
        # )
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
            # current_user["id"] = existing_user[0]
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
            Clock.schedule_once(
                lambda dt: setattr(
                    self.manager,
                    "current",
                    "welcome"
                )
            )

        except Exception as e:
            print("Google Login Cancelled or Failed",e)
            # stay on login screen
            self.manager.current = "login"



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
        name=self.ids.signup_name.text
        email=self.ids.signup_email.text.strip().lower()
        phone=self.ids.signup_phone.text
        password=self.ids.signup_password.text
        # Empty field check
        if name=="" and email=="" and phone=="" and password=="":
            show_popup(title="required",message="Please fill all fields")
            return

        cursor.execute("SELECT * FROM users WHERE email=?",(email,))
        existing = cursor.fetchone()
        if existing:
            show_popup(title="",message="Email already exists")
            self.ids.signup_name.text = ""
            self.ids.signup_email.text = ""
            self.ids.signup_phone.text = ""
            self.ids.signup_password.text = ""
        else:
            (cursor.execute
             ("INSERT INTO users (name, email, phone, password) VALUES(?,?,?,?)",(name,email,phone,password)
                ))
            conn.commit()
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

    def __init__(self, **kw):
        super().__init__(**kw)
        self.open_menu = None
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

        self.dialog.open()


    def connect_gmail(self):
        gmail_btn=self.ids.gmail_btn
        user_email = current_user["email"]
        save_credentials(user_email)
        gmail_btn.text="Gmail Connected"
        gmail_btn.disabled = True
        
    def email_checkbox(self):
        check_box=self.ids.email_cb
        # email_btn=self.ids.email_btn.text
        check_box.active=not check_box.active
        if check_box.active:
            user_email=current_user["email"]
            save_credentials(user_email)

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
            formatted_date=actual_date.strftime("%y-%m-%d")
            self.ids.wish_date.text=formatted_date
        instance_date_picker.dismiss()

    @staticmethod
    def on_date_cancel(instance_date_picker):
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

    @staticmethod
    def on_time_cancel(instance_time_picker):
        instance_time_picker.dismiss()

    def close_side_menu(self):
        if self.ids.side_panel.opacity==1:
            self.side_menu()

    def side_menu(self):
        menu_btn=self.ids.menu_btn
        side_panel=self.ids.side_panel
        over_lay=self.ids.overlay
        # wish_content=self.ids.wish_content
        if not self.open_menu:
            # side_panel.opacity=1
            side_panel.disabled = False
            #over_lay.disabled = False
            over_lay.size_hint=1,1
            over_lay.size=Window.size
            #wish_content.disabled = True
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
            # side_panel.opacity=0
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
            over_lay.size_hint=None,None
            over_lay.size=(0,0)
            # over_lay.disabled = True
            side_panel.disabled = True
            # wish_content.disabled = False
            self.open_menu=False


            menu_btn.background_normal="image/menu.png"
            menu_btn.background_down="image/menu.png"


    def schedule_wish(self):
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
            "INSERT INTO wishes(name,phone,recipient_email,message,subject,date,time,Platform) VALUES(?,?,?,?,?,?,?,?)",
            (name, phone,recipient_email,message,subject, date, tim, mode)
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
        label = self.ids.welcome_label

        # Start invisible
        label.opacity = 0
        label.scale=0.5

        # Fade in animation
        anim = Animation(opacity=1,scale=1.2, duration=1) + \
               Animation(scale=1, duration=0.3)

        anim.start(label)

        # After 2 seconds → go to Add Wish screen
        Clock.schedule_once(self.go_next, 2.5)

    def go_next(self,_dt):
     self.manager.current = "home"


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
        self.menu_open = None

    def close_side_menu(self):
        if self.menu_open:
            self.side_menu()

    def side_menu(self):
        menu_btn=self.ids.menu_btn
        side_panel=self.ids.side_panel
        over_lay=self.ids.overlay
        # content=self.ids.home_content
        if side_panel.opacity==0:
            # side_panel.opacity=1
            side_panel.disabled = False
            over_lay.disabled = False
            # Animation(
            #     x=260,
            #     duration=0.3,
            #     t="out_cubic"
            #
            # ).start(content)
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
            over_lay.disabled = True
            self.menu_open = False
            menu_btn.background_normal="image/menu.png"
            menu_btn.background_down="image/menu.png"

    def on_pre_enter(self, *args):
        self.total_wishes()
        self.pending_wishes()
        self.sent_wishes()
        self.failed_wishes()

    def total_wishes(self):
        try:
            conn8 = sqlite3.connect("user.db")
            cursor8 = conn8.cursor()
            cursor8.execute("SELECT COUNT(*) FROM wishes")
            total = cursor8.fetchone()[0]
            self.ids.wish_number.text=str(total)
        except Exception as e:
            print(e)
    def pending_wishes(self):
        try:
            conn9=sqlite3.connect("user.db")
            cursor9=conn9.cursor()
            cursor9.execute("""SELECT COUNT(*) FROM wishes WHERE status='Pending'""")
            total=cursor9.fetchone()[0]
            self.ids.pending_number.text=str(total)
        except Exception as e:
            print(e)

    def sent_wishes(self):
        try:
            conn10=sqlite3.connect("user.db")
            cursor10=conn10.cursor()
            cursor10.execute("SELECT COUNT(*) FROM wishes WHERE status='Success'")
            total=cursor10.fetchone()[0]
            self.ids.sent_number.text=str(total)
        except Exception as e:
            print(e)

    def failed_wishes(self):
        try:
            conn11=sqlite3.connect("user.db")
            cursor11=conn11.cursor()
            cursor11.execute("SELECT COUNT(*) FROM wishes WHERE status='Failed'")
            total=cursor11.fetchone()[0]
            self.ids.failed_number.text=str(total)
        except Exception as e:
            print(e)

    def on_enter(self,*args):

        full_name = str(current_user["name"]).split()
        first_name = full_name[0]
        home_label = self.ids.home_label
        home_label.text=f"Welcome, {first_name}"
        self.ids.profile.text=first_name
        self.manager.current = "home"

    # Factory.register('ProfileSpinnerOption', cls=ProfileSpinnerOption)

    def on_spinner_select(self, text):
        if text == "Edit Profile":

            # Safely switch screens without weak reference crashes
            self.manager.current = "edit_profile"



    # def change_screen_and_dismiss(self):
    #     self.ids.drop.__self__.dismiss()
    #     self.manager.current = "edit_profile"

class EditProfileScreen(Screen):

    def on_pre_enter(self,*args):
        self.ids.full_name.text = current_user["name"]
        self.ids.email.text = current_user["email"]
        self.ids.phone.text = current_user["phone"]

    def update_profile(self):

        name = self.ids.full_name.text.strip()
        email = self.ids.email.text.strip()
        phone = self.ids.phone.text.strip()

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
    selected_color = "Blue"

    def refresh_language(self):
        t = App.get_running_app().language.translate
        self.ids.save.text=t("Save Settings")
        self.ids.restore.text=t("Restore Default")
        self.ids.accent.text=t("Accent Color")
        if self.ids.language_spinner.text=="Hindi":
            self.ids.language_spinner.text=t("Hindi")
        else:
            self.ids.language_spinner.text=t("English")
        self.ids.font_size.text=t("Font Size")
        if self.ids.font_value.text==range(11,30):
            self.ids.font_slider.value=t(11,30)
        self.ids.font_value.text=t("18")
        self.ids.personalize.text=t("Personalize")

    def background_theme(self):
        theme=self.ids.theme_spinner.text
        login=self.manager.get_screen("login")
        signup=self.manager.get_screen("signup")
        welcome=self.manager.get_screen("welcome")
        addwish=self.manager.get_screen("add_wish")
        home=self.manager.get_screen("home")
        forgotpassword=self.manager.get_screen("forgot")
        editprofile=self.manager.get_screen("edit_profile")
        personalize=self.manager.get_screen("personalize")


        if theme=="Dark":
            login.ids.image.source="image/wisher-dark-bg.jpg"
            login.ids.login_email.foreground_color=(1,1,1,1)
            login.ids.login_password.foreground_color=(1,1,1,1)

            signup.ids.image.source="image/wisher-dark-bg.jpg"
            signup.ids.signup_name.foreground_color=(1,1,1,1)
            signup.ids.signup_email.foreground_color=(1,1,1,1)
            signup.ids.signup_password.foreground_color=(1,1,1,1)
            signup.ids.signup_name.foreground_color=(1,1,1,1)
            signup.ids.signup_phone.foreground_color=(1,1,1,1)

            addwish.ids.image.source="image/wisher-dark-bg.jpg"
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

            forgotpassword.ids.image.source="image/wisher-dark-bg.jpg"
            forgotpassword.ids.fp_email.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.otp_input.foreground_color = (1, 1, 1, 1)
            forgotpassword.ids.new_password.foreground_color = (1, 1, 1, 1)

            welcome.ids.image.source="image/wisher-dark-bg.jpg"

            editprofile.ids.image.source="image/wisher-dark-bg.jpg"
            editprofile.ids.full_name.foreground_color = (1, 1, 1, 1)
            editprofile.ids.email.foreground_color = (1, 1, 1, 1)
            editprofile.ids.phone.foreground_color = (1, 1, 1, 1)

            personalize.ids.image.source="image/wisher-dark-bg.jpg"


        elif theme=="Light":
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

    def select_color(self, color):
        self.selected_color = color
        print("Selected:", color)

    def restore_default(self):
        self.ids.theme_spinner.text = "Light"
        self.ids.language_spinner.text = "English"
        self.ids.font_slider.value = 18
        self.selected_color = "Blue"

    def save_settings(self):
        theme = self.ids.theme_spinner.text
        language = self.ids.language_spinner.text
        font_size = int(self.ids.font_slider.value)
        conn9 = sqlite3.connect("user.db")
        cursor9 = conn9.cursor()

        cursor9.execute("""
        INSERT OR REPLACE INTO personalize
        (user_id,theme,language,font_size,accent_color)
        VALUES(?,?,?,?,?)
        """,(
                           current_user["id"],
                           theme,
                           language,
                           font_size,
                           self.selected_color
                       ))

        conn9.commit()
        conn9.close()
        App.get_running_app().language.current_language = language
        self.manager.current = "home"

        print(theme)
        print(language)
        print(font_size)
        print(self.selected_color)



class HistoryScreen(Screen):


    def on_pre_enter(self, *args):
        self.load_history()

    def load_history(self):
        self.ids.history_container.clear_widgets()
        conn10 = sqlite3.connect("user.db")
        cursor10 = conn.cursor()

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
            FROM wishes
            ORDER BY date DESC,time DESC
            """)
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
            WHERE LOWER(name) LIKE ?
            """, ("%"+keyword+"%", ))

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
    def on_enter(self, *args):
        self.show_general()

    def show_notification(self):
        self.ids.content_area.clear_widgets()
        self.ids.content_area.add_widget(NotificationContent())
        self.ids.save_btn.opacity = 1
        self.ids.save_btn.disabled = False

        self.current_tab = "notification"

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
        self.ids.save_btn.opacity = 1
        self.ids.save_btn.disabled = False

        self.current_tab = "general"

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
        self.ids.save_btn.opacity = 1
        self.ids.save_btn.disabled = False

        self.current_tab = "advanced"

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
    pass

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
        cursor12 = conn.cursor()

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

    # if minimize_to_tray:
    #     if tray==1:
    #         Window.hide()
    #     else:
    #         App.get_running_app().stop()

class AboutContent(BoxLayout):

    @staticmethod
    def rate_app():
        print("Rate App Clicked")

    @staticmethod
    def share_app():
        print("Share App Clicked")

scheduler_thread= threading.Thread(target=scheduler.run)
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
        scheduler_status=self.ids.scheduler_status
        if scheduler_thread is None or not scheduler_thread.is_alive():
            scheduler_stop_event.clear()
            scheduler_thread = threading.Thread(target=run_scheduler,daemon=True).start()
            print("Scheduler Started")
            scheduler_status.text="Running"




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
    pass
    # def switch_to_login(self):
    #     self.current = "login"
    #
    # def switch_to_signup(self):
        # self.current = "signup"
    #
    # def switch_to_dashboard(self):
    #     self.current = "dashboard"


# def send_message(wish):
#     name, phone, message = wish[1], wish[2], wish[3]
#     date = wish[4]
#     time_str = wish[5]
#
#     # convert time
#     hour, minute = map(int, time_str.split(":"))
#
#     print(f"Sending WhatsApp message to {name}")
#
#     send_whatsapp_message(phone, message, hour, minute)
#
#     print(f"Sending message to {name}: {message}")

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
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        scopes
    )
    creds = flow.run_local_server(port=0)
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



scopes=["https://www.googleapis.com/auth/gmail.send"]

def send_message(wish):
    name = wish[1]
    recipient_phone = wish[2]
    recipient_email=wish[3]
    message = wish[4]
    subject = wish[5]
    plat_form=wish[8].split(",")

    conn5=sqlite3.connect("user.db")
    cursor5=conn5.cursor()
    whatsapp_uri=F"whatsapp://send?phone={recipient_phone}"


    if "WhatsApp" in plat_form:
        try:
            print(f"Opening WhatsApp for {name}")
            # Trigger Windows to open the URI with the WhatsApp desktop application
            subprocess.Popen(["cmd", "/C", f"start {whatsapp_uri}"], shell=True)
            # Wait for the desktop application to open and load the chat window
            time.sleep(10)
            # it touches the chat window
            pyautogui.click()
            # Type the message automatically
            pyautogui.typewrite(f"{message}")

            time.sleep(1)
            # Press enter to send the message
            pyautogui.press('enter')

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
                print("No Gmail account connected")
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

    # if "SMS" in plat_form:
    #     bird=Bird(api_key="bk_us1_V4r5EyYF6q2xOx7CjrM83LE25beY2")
    #     bird.sms.send(
    #         to=recipient_phone,
    #         msg={
    #
    #         }
    #     )


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
    for wish in all_wishes:
        wish_id = wish[0]
        name = wish[1]
        # phone = wish[2]
        # message = wish[3]
        date = wish[6]
        time_str = wish[7]
        plat_form=wish[8].split(",")

        try:
            # Combine date + time
            wish_time = datetime.strptime(f"{date} {time_str}", "%Y-%m-%d %H:%M:%S %p")


        except ValueError:
            print(f"Invalid date/time format {date} {time_str}")
            conn1.commit()
            continue


        if wish_time > now:
            cursor1.execute("""UPDATE wishes SET status="Pending" WHERE id=?""", (wish_id,))
            conn1.commit()
            continue
            # ⏱ Check if within 1-minute window
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
    conn1.close()

scheduler_stop_event=threading.Event()

def run_scheduler():

    while not scheduler_stop_event.is_set():
        try:
            check_wishes()
        except Exception as e:
            print("Scheduler Error:", e)

        time.sleep(1)  # check every 30 seconds (better accuracy)   # check every minute

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
            Item("Open", self.restore_window),
            Item("Exit", self.exit_app)
        )
        self.tray_icon = pystray.Icon(
            "Wisher",
            image,
            "Wisher App",
            menu
        )

        self.tray_icon.run()

    def on_start(self):
        conn16 = sqlite3.connect("user.db")
        cursor16 = conn16.cursor()

        cursor16.execute("""
        SELECT auto_scheduler
        FROM general_settings
        WHERE id=1
        """)

        row = cursor16.fetchone()


        if row[0]==1:
            threading.Thread(
                target=run_scheduler,
                daemon=True
            ).start()
        # threading.Thread(target=run_scheduler, daemon=True).start()
            reset_scheduler_status()
        # else:
        #     cursor16.execute("""
        #     UPDATE advanced_settings SET scheduler_status = 'Stopped' WHERE id=1""")
        #     conn16.commit()

        conn16.close()


    def on_language_changed(self,*args):
        if not self.root:
            return
        for screen in self.root.screens:
            if hasattr(screen,"refresh_language"):
                screen.refresh_language()
if __name__ == '__main__':
    WisherApp().run()

