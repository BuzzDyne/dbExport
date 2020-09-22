from firebase_admin import auth

class AuthModule:

    def createUser(self, userEmail, userPw):
        """Creates a new user and returns its uid"""
        user = auth.create_user(email= userEmail, password= userPw)
        
        # print('ID: {}'.format(user.uid))
        # print('Email: {}'.format(user.email))
        # print('User: {}'.format(user))
        
        return user.uid