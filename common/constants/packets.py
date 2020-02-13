client_login = 1 # Client login request to the server
client_logout = 2 # Client logout request to the server

# Server login responses
server_loginSuccess = 3
server_loginInvalidData = 4
server_loginNoSuchUsername = 5
server_loginIncorrectPassword = 6
server_loginBanned = 7

# Server basic user information to the client (userID, online players).
server_sendUserInfo = 8

# Get an INT16_LIST of all users online.
client_getOnlineUsers = 9
server_sendOnlineUsers = 10

client_addBottle = 11
