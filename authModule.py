from firebase_admin import auth

class AuthUser:
    def __init__(self, userEmail, userPw, userEmailVerified=None, userPhone=None, userDisplayName=None, userPhotoUrl=None, userDisabled = None):


        self.email  = userEmail
        self.pw     = userPw

        self.email_verified=False
        self.phone_number='+15555550100'
        self.displayName='John Doe'
        self.photoUrl='http://www.example.com/12345678/photo.png'
        self.disabled=False