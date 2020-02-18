# If a packet starts with 'client', it is client -> server.
# Otherwise, it is server -> client.

client_login = 1
client_logout = 2

server_generalSuccess = 3
server_generalFailure = 4
server_generalInvalidArguments = 5
server_generalNoSuchUsername = 6
server_generalIncorrectPassword = 7
server_generalBanned = 8

# Server basic user information to the client (userID, online players).
server_sendUserInfo = 9

# Get an INT16_LIST of all users online.
client_getOnlineUsers = 10
server_sendOnlineUsers = 11

client_registerAccount = 12
server_registrationUsernameTaken = 13

# Create a new bottle.
client_addBottle = 14

# Request a list of our inventory of incomplete bottles.
client_getInventory = 15
server_sendInventory = 16

# Take a shot! B)
client_takeShot = 17

client_getLedger = 18
server_sendLedger = 19

server_alreadyUpToDate = 20
