#author Jonathan Israel E. Serrano <- full stack game dev/SPA web dev
#JSON driven socket and websocket program
#JSON is THE BEST
#images can be converted to svg strings
#that's the magic behind this
#dependency desu
#pip install them depependencies
#-install eventlets first
#pip install eventlet
#pip install flask-socketio
#pip install Flask
#pip install Pyro4#pip install flask-socketio
def selfInstallDependencies():
    print("attemping to self install depedencies")
    import pip
    pip.main(['install', 'eventlet'])    
    pip.main(['install', 'flask-socketio'])    
    pip.main(['install', 'Flask'])     
    #pip.main(['install', 'Pyro4'])
try:
    import eventlet
except:
    selfInstallDependencies()

from flask import Flask,redirect,current_app,session
from flask_socketio import SocketIO,send,emit,join_room #as sendToHTML
import threading,webbrowser,time,json#,socket
from eventlet.green import socket

from eventlet import tpool

import socket as sck
import eventlet
import time
import classDesu.Bounds
import classDesu.Platforms
import classDesu.ActorBase
import classDesu.GameEnvironment
import classDesu.Map_hell
import classDesu.Map_cem
import classDesu.Map_grassy
import classDesu.Map_storm
import classDesu.Map_warfield
import classDesu.Map_snow
import classDesu.Map_sea
import classDesu.Map_moon
import traceback
import sqlite3
import time
eventlet.monkey_patch()

import os
#print(os.listdir("/"))
#print( __file__ )

print( os.path.dirname(__file__) )

#image and sound cache code
["img/sadaasd/ff.png"]



#print(os.path.realpath(os.path.basename(os.path.dirname(os.path.realpath(__file__)))) )

#Central Server Node mode
gamecentral = None

#Gameplayer Node mode
gameplayer = None

#Player Code
room = None
game = None

#Developper mode code
devMode = True
#game mode states if client or server mode
gameMode = None
bgm = "snd/re.mp3"

def getBgm(rg):
    js_snd({"do":"getBgm","data":bgm})

def chngChar(rq):
    if game != None and devMode == True and room.tcpCon == None and room.tcpServerChan == None:
        game.dev_changeChara()    

#detects and applies key press to charcater

def canvasKey(rq):
    global room
    
    if(game != None):
        if(game.current != None):
            game.current.keys[rq['data'][0]] = rq['data'][1]
              
    if(gameplayer != None and gameplayer.name != ''):
        sckt_sendToOtherSocket({'data':[{'do':'cntsrv_keypress','data':{
            'name':gameplayer.name,
            'p0':rq['data'][0],
            'p1':rq['data'][1]
            }}]},gameplayer.tcpCon)
        
militime = lambda: int(round(time.time() * 1000))

def checkServOnline(rq):
    global gameplayer
    rs = checkIPadress(rq['data']['server'],rq['data']['port'])
    print('serv is',rs)    
    gameplayer.isServViable = rs
    js_snd({'do':'checkServOnline','data':rs})
    
def checkIPadress(server,port):
    try:
        tcpCon = socket.socket()
        tcpCon.connect((server,port))
        tcpCon.close()
        return True
    except Exception as e:
        return False    

def updateGameThread_():
    while 1:
        start = militime()
        game.update()
        end = militime()
        sleep = (28-(end-start))
        if sleep > 0:
            time.sleep(sleep/1000)
        print('time used:'+str(end-start))
        
def updateGameThread():
    while 1:
        start = militime()
        
        if(game != None and (gameplayer.roomInfo==None or gameplayer.roomInfo['gameStarted']==False)):
            def gg():
                game.update()
                js_snd(game.getDrawAbles())
            eventlet.spawn_n(gg)
            
#        if(gamecentral != None):
#            gamecentral.cntsrv_updateAndRenderGames()
        
        end = militime()
        #print('time used:'+str(end-start))
        #35 fps updates and rendering
        sleep = (28-(end-start))
        if sleep > 0:
            eventlet.greenthread.sleep(sleep/1000)

def adjustCanvas(rq):
    global gameplayer    
    if game != None:
        game.cmra.width = rq['data'][0]        
        game.cmra.height = rq['data'][1]
    
    if gameplayer != None:
        gameplayer.cmra.width = rq['data'][0]        
        gameplayer.cmra.height = rq['data'][1]
        gameplayer.plyr_adjustCanvas(None)
        
    js_snd(rq)

def addUser(user,pw):
    pass     
        
def setUser(pw,ptskiller,ptsDefender,ptsRunner):
    pass

def getUser(user):
    pass
        
def rm_canvasKey(rq):
    try:
        #print('recive client keypress',rq)
        room.keyPressClient(rq['data']['name'],rq['data']['p0'],rq['data']['p1'])
    except Exception as e:
        print(e)
        traceback.print_tb(e.__traceback__)

app = Flask(__name__, static_url_path="")
#assigns route to stupid root
@app.route( '/' )
def hello():
    #if not game.gamestarted:
    eventlet.spawn_n(updateGameThread)
    #threading.Thread(target=updateGameThread_).start()
    return redirect("index.html")
#print('current key is',app.config['SECRET_KEY'])
#app.config['SECRET_KEY'] = 'mynameismimingcatmeow'
#no secret key is faster this not online anyway
#fast transfer of SVG images is priority over encryption
#async_mode='threading' """#
#async_mode='eventlet' <- autoselected
socketio = SocketIO(app)
clnt_threadLock = threading.Lock()

#central server and player node listenner thread
#special actions that require connection to be monitored
conRequired = ['cntsrv_login','cntsrv_createRoom','cntsrv_joinRoom']

def getFxn(do):
    fxn = None
    if(do.startswith('plyr_')):
        fxn = getattr(gameplayer,do)    
    elif(do.startswith('cntsrv_')):        
        fxn = getattr(gamecentral,do)  
    else:
        fxn = globals()[do]
    return fxn

def waitRoomMsgNode(conn):
    data = ''
    print('==Room awaiting msg==')
    while 1:
        #print('waiting for msg desu')
        try: 
            rd = conn.recv(4096)                
            if rd:
                read = rd.decode('utf-8')
                data += read                    
                while '[[the_end]]' in data :
                    splt = data.split('[[the_end]]',maxsplit=1)                
                    proc = splt[0]                
                    data = splt[1]
                    res = json.loads(proc)                        
                    for rq in res['data']:
                        fxn = getFxn(rq['do'])
                        if rq['do'] in conRequired:
                            rq['con'] = conn       
                        try:                     
                            rs = fxn(rq)
                        except Exception as ex:
                            print(ex)
                            traceback.print_tb(ex.__traceback__)
            elif not rd:
                print("socket is dead? i dunno")                                    
                #conn.close()                
                #print("socket is closed")   
                return
        except Exception as e:
            pass
            #print('exeption happened')
            #print(e)
                                 
    conn.close()
    print('exiting thread')

class GameCentral(object):
    def __init__(self):
        self.tcpServerChan = None
        #room model
        #{'game':None,'chatBox':[],'selectedLoc':'hell','maxPlayers':'','time':15,'host':''}
        #game id is the milli time
        self.rooms = {}
        
        #client model
        #{'con':None,'cmra':None,'currentChar':'','char_type':'miming','name':'','room':''}
        self.clients = {}
                
        self.dbcon = sqlite3.connect('koth.db')
        self.cursor = self.dbcon.cursor()
        
    def cntsrv_startServ(self,port=9000):
        self.tcpServerChan = eventlet.listen(('',port))                     
        serverIP,serverPort = self.tcpServerChan.getsockname()
        print('===>CENTRAL SERVER MODE initiated!:[',serverIP,':',serverPort,']<===')                        
        def waitRoomClient():
            while 1:  
                try:
                    print('CENTRAL SERVER waiting for client')
                    conn, addr = self.tcpServerChan.accept()
                    conn.setblocking(0)
                    conn.settimeout(.5)                                           
                    eventlet.spawn_n(lambda:waitRoomMsgNode(conn))
                    ip,port=conn.getpeername()
                    print('CENTRAL SERVER client has connected peer is>>',ip,port)
                except Exception as e:
                    print(e)      
        eventlet.spawn_n(waitRoomClient)
        js_snd({'do':'cntsrv_selfInit'})
        
        
    def cntsrv_toJSONrooms(self):
        rooms = {}
        for key, room in self.rooms.items():
            rm = room.copy()
            
            rm['gameStarted'] = (rm['game'] != None)            
            if(rm['game'] != None):
                rm['timeleft'] = rm['game'].timerLeft  
            
            rm.pop('game',None)            
            rm.pop('chatBox',None)
                 
            rooms[key] = rm
        return rooms
        
    def cntsrv_createRoom(self,rq):
        room = {
            'game':None,
            'chatBox':[{'usr':rq['data']['name'],'act':'created room'}],
            'selectedLoc':'hell',
            'maxPlayers':8,
            'time':15, #in minutes
            'host':rq['data']['name']
            }
        
        id = militime()      
        
        while id in self.rooms.keys():
            id+=1
        
        self.rooms[id]=room        
        rq['data']['id'] = id
        print('new room created')        
        self.cntsrv_toAllclients({'do':'plyr_roomsSync','data':self.cntsrv_toJSONrooms()})    
        self.cntsrv_joinRoom(rq)
        
    def cntsrv_startGame(self,rq):
        roomID = rq['data']['id']        

        rm = self.rooms[roomID]
        
        if(rm['selectedLoc'] == 'hell'):
            rm['game'] = classDesu.Map_hell.Map_hell()
        elif(rm['selectedLoc'] == 'cem'):
            rm['game']  = classDesu.Map_cem.Map_cem()
        elif(rm['selectedLoc'] == 'grass'):
            rm['game']  = classDesu.Map_grassy.Map_grassy()
        elif(rm['selectedLoc'] == 'storm'):
            rm['game']  = classDesu.Map_storm.Map_storm()
        elif(rm['selectedLoc'] == 'war'):
            rm['game']  = classDesu.Map_warfield.Map_warfield()
        elif(rm['selectedLoc'] == 'snow'):
            rm['game']  = classDesu.Map_snow.Map_snow()    
        elif(rm['selectedLoc'] == 'sea'):
            rm['game']  = classDesu.Map_sea.Map_sea()
        elif(rm['selectedLoc'] == 'moon'):
            rm['game'] = classDesu.Map_moon.Map_moon()
            
        rm['game'].timerLeft = rm['time'] * 35 * 60
        rm['game'].pausegame = True
        rm['game'].gamestarted = True

        #members = [x for x in self.clients if x['room'] == roomID]
        #for member in members:
        #    self.cntsrv_startGame_joinChara(member['name'])
            
        for key,clnt in self.clients.items():
            if(clnt['room']== roomID):
                self.cntsrv_startGame_joinChara(clnt['name'])
        
        self.cntsrv_syncRoom(roomID)
        
    def cntsrv_startGame_joinChara(self,name):
        clnt = self.clients[name]
        rm = self.rooms[clnt['room']]
        chr = rm['game'].addCharacter(clnt['name'],clnt['char_type'])
        clnt['currentChar'] = chr
        print("character joined game",name)
        
    def cntsrv_leaveRoom(self,rq):
        name = rq['data']['name']
        roomID = self.clients[name]['room']
        self.clients[name]['room'] = None
        self.rooms[roomID]['chatBox'].append({'usr':name,'act':'left the room'})
        self.cntsrv_syncRoom(roomID)
    
    def cntsrv_toAllclients(self,jsn):
        for key, clnt in self.clients.items():   
            con = clnt['con']
            eventlet.spawn_n(sckt_sendToOtherSocket,jsn,con)
    
    def cntsrv_joinRoom(self,rq):
        id = rq['data']['id']
        joinSucces = False
        
        if id in self.rooms.keys() and self.clients[rq['data']['name']]['room'] == None:
            self.clients[rq['data']['name']]['room'] = id
            joinSucces = True
            
        data = {}            
        con = rq['con']
        if(joinSucces == True):
            self.rooms[id]['chatBox'].append({'usr':rq['data']['name'],'act':'joined room'})
            roomInfo = self.rooms[id].copy()
            roomInfo['id'] = id
            roomInfo['gameStarted'] = (self.rooms[id]['game'] != None)            
            gm = roomInfo.pop('game',None)
            data['roomInfo'] = roomInfo
            
            #if game is already ongoing
            if( gm != None):
                self.cntsrv_startGame_joinChara(rq['data']['name'])
            print('SRV user joined room',rq['data']['name'])
            
            self.cntsrv_syncRoom(id)
        else:
            print('SRV user failed to join room',rq['data']['name'])
    
    def cntsrv_chngeRoom(self,rq):
        name = rq['data']['name']        
        cht = {'usr':name}        
        roomID = self.clients[name]['room']
        rm = self.rooms[roomID]
        
        updateAll = False
        
        if('msg' in rq['data']):
            cht['msg'] = rq['data']['msg']
            
        if('selectedLoc' in rq['data']):
            cht['act'] = 'changed location to '+rq['data']['selectedLoc']
            rm['selectedLoc'] = rq['data']['selectedLoc']
            updateAll = True
            
        if('maxPlayers' in rq['data']):
            cht['act'] = 'changed max players to '+str(rq['data']['maxPlayers'])
            rm['maxPlayers'] = rq['data']['maxPlayers']
            updateAll = True
        
        if('time' in rq['data']):
            cht['act'] = 'changed play time to '+str(rq['data']['time'])
            rm['time'] = rq['data']['time']
            updateAll = True
        
        rm['chatBox'].append(cht)
        
        self.cntsrv_syncRoom(roomID)      
        if(updateAll):
            self.cntsrv_toAllclients({'do':'plyr_roomsSync','data':self.cntsrv_toJSONrooms()})
    
    def cntsrv_syncRoom(self,roomID):
        data = {}
        roomInfo = self.rooms[roomID].copy()
        roomInfo['id'] = roomID
        roomInfo['gameStarted'] = (self.rooms[roomID]['game'] != None)   
        roomInfo['players'] = []
        
        for key,clnt in self.clients.items():
            if(clnt['room']==roomID):
                roomInfo['players'].append([key,clnt['char_type']])
        
        gm = roomInfo.pop('game',None)
        data['roomInfo'] = roomInfo
        self.cntsrv_sendToRoomMembers(roomID,{'do':'plyr_roomSync','data':data})
    
    def cntsrv_sendToRoomMembers(self,roomID,jsn):
        for key,clnt in self.clients.items():
            if(clnt['room'] == roomID):
                eventlet.spawn_n(sckt_sendToOtherSocket,jsn,clnt['con'])
    
    def cntsrv_login(self,rq):
        name = rq['data']['name']
        con = rq['con'] 
        
        #even if user is valid program prevents double log in
        #also validate if connection is already associated with a 
        #user
        
        conIsUnique = True            
        isValidLogin = True and name not in self.clients.keys() and conIsUnique
        
        if(isValidLogin):
            #adding user to userlist
            print('user added in server mode',name,con.getpeername())    
            self.clients[name] = {
                'con':con,
                'currentChar':None,
                'char_type':'miming',
                'name':name,
                'cmra':classDesu.Bounds.Bounds(0,0,rq['data']['width'],rq['data']['height']),
                'room':None
                }
            print('all users',len(self.clients))     
        else:
            print('user was not added in server mode',name)  
            
        data = [{'do':'plyr_login','data':{
                'name':name,
                'loginSuccess':isValidLogin,
                'srvValidated':1                    
                }}]
        
        if(isValidLogin == True):
            data.append({'do':'plyr_roomsSync','data':self.cntsrv_toJSONrooms()});            
        sckt_sendToOtherSocket({'data':data},con)

    def cntsrv_keypress(self,rq):
        chr = self.clients[rq['data']['name']]['currentChar']        
        if(chr != None):        
            chr.keys[rq['data']['p0']] = rq['data']['p1']

    def cntsrv_adjustCanvas(self,rq):
        cmra = self.clients[rq['data']['name']]['cmra']
        cmra.width = rq['data']['width']
        cmra.height = rq['data']['height']
            
    def cntsrv_logout(self,rq):
        self.clients.pop(rq['data']['name'],None)
        print('SERV:player logged out',rq['data']['name'])
    
    def cntsrv_updateAndRenderGames(self):
        def cntsrv_updateAndRenderGame(game,roomID):
            #def gg():
            start = militime()
            game.update()
            end = militime()
            print('took ',(end-start),' millis')
                        
            def drawClient(name):
                clnt = self.clients[name]        
                if clnt['currentChar'] != None:        
                    rq=game.getDrawAbles(clnt['cmra'],clnt['currentChar'])
                    sckt_sendToOtherSocket({'data':[{'do':'js_direct','data':rq}]},clnt['con'])
            
            for key,clnt in self.clients.items():
                if(clnt['room'] == roomID):
                    eventlet.spawn_n(drawClient,clnt['name'])
        
        for key,room in self.rooms.items():
            if(room['game'] != None):
                eventlet.spawn_n(cntsrv_updateAndRenderGame,room['game'],key)
        
def cntsrvP_startServ(rq):
    global gamecentral    
    if(gamecentral == None):
        gamecentral = GameCentral()
        gamecentral.cntsrv_startServ(rq['data']['port'])     
    else:
        print("==>Game Center already online")
        
def cntsrvP_stopServ(rq):
    global gamecentral    
    if(gamecentral != None):   
        gamecentral.tcpServerChan.close()
        gamecentral.cursor.close()
        gamecentral.dbcon.close()
        for key,clnt in gamecentral.clients.items():
            clnt['con'].close()
        gamecentral = None  
        print("==>Game Center stopped")          
    else:
        print("==>Game Center already stopped")

class GamePlayer(object):
    def __init__(self):
        #PC Node mode
        self.isServViable = False
        self.tcpCon = None
        self.name = ''
        self.selectedChar = 'miming'
        self.cmra = classDesu.Bounds.Bounds(0,0,600,800)
        self.currentBGM = ''
        
        self.game=None
        
        #room model
        #{'gameStarted':None,'selectedLoc':'hell','maxPlayers':'','time':15,'host':''}
        self.rooms = {}
        
        #room info model
        #same as from central server
        self.roomInfo = None
        
        #outroom|inroom|ingame
        self.state = 'login'
        
    #simply starts connection not login itself
    def plyr_start(self,rq):
        server = rq['data']['server']
        port = rq['data']['port']
        rs = False
          
        if(self.tcpCon != None):
            return
        try:
            print('===>CLIENT MODE initiated!:[',server,':',port,']<===')            
            self.tcpCon = socket.socket()
            self.tcpCon.connect((server,port))
            self.tcpCon.setblocking(0)
            self.tcpCon.settimeout(.5)    
            eventlet.spawn_n(waitRoomMsgNode,self.tcpCon)
            rs = True
        except Exception as e:
            self.tcpCon = None
            print('===>CLIENT MODE initiated failed to connect<===')  
            rs = False
        #js_snd({'do':'plyr_start','data':rs})
        self.plyr_loadState(None)
        
    def plyr_login(self,rq):
        #server validated return code  
        print('player trying to log-in')
        
        if('srvValidated' in rq['data'].keys()):
            if(rq['data']['loginSuccess'] == True):
                self.name = rq['data']['name']
                self.state = 'outroom'
                
            js_snd(rq)
        else:
            print('player trying to log-in via server')
            sckt_sendToOtherSocket({'data':[{'do':'cntsrv_login','data':{
                    'name':rq['data']['name'],
                    'password':rq['data']['password'],
                    'width':self.cmra.width,
                    'height':self.cmra.height     
                    }}]},self.tcpCon)
        
    def plyr_loadState(self,rq):
        serverIP = ''
        serverPort = ''
        
        if(self.tcpCon != None):
            serverIP,serverPort = self.tcpCon.getpeername()        
        
        js_snd({'do':'plyr_loadState','data':{
            'name':self.name,
            'isServViable':self.isServViable,
            'isConnected':self.tcpCon != None,
            'state':self.state,
            'serverIP':serverIP,                
            'serverPort':serverPort,
            'rooms':self.rooms,
            'roomInfo':self.roomInfo
            }})
        
    def plyr_roomSync(self,rq):
        #print('recieving room info')        
        if 'roomInfo' in rq['data']:
            self.roomInfo = rq['data']['roomInfo']
            #print(rq)
        js_snd(rq)
        
    def plyr_roomsSync(self,rq):
        self.rooms = rq['data']
        js_snd(rq)
        
    def plyr_createRoom(self,rq):
        sckt_sendToOtherSocket({
            'do':'cntsrv_createRoom',
            'data':{'name':self.name}},self.tcpCon)
        
    def plyr_logout(self,rq):
        rq['data'] = {'name':self.name}
        gameplayer.name = ''
        js_snd(rq)        
        rq['do'] = 'cntsrv_logout'        
        sckt_sendToOtherSocket(rq,self.tcpCon)
        
    def plyr_joinRoom(self,rq):
        sckt_sendToOtherSocket({
            'do':'cntsrv_joinRoom',
            'data':{
                'name':self.name,
                'id':rq['data']['id']
            }
        },self.tcpCon)
        
    def plyr_startGame(self,rq):
        sckt_sendToOtherSocket({
            'do':'cntsrv_startGame',
            'data':{'id':self.roomInfo['id']}
        },self.tcpCon)
        
    def plyr_leaveGame(self,rq):
        self.roomInfo = None
        sckt_sendToOtherSocket({
            'do':'cntsrv_leaveRoom',
            'data':{'name':self.name}
        },self.tcpCon)
        self.plyr_loadState(None)
        
    def plyr_chngeRoom(self,rq):
        rq['do'] = 'cntsrv_chngeRoom'
        rq['data']['name'] = self.name
        sckt_sendToOtherSocket(rq,self.tcpCon)
     
    def plyr_adjustCanvas(self,rq):
        if(self.name != ''):
            sckt_sendToOtherSocket({'data':[{'do':'cntsrv_adjustCanvas','data':{
            'name':self.name,
            'width':self.cmra.width,
            'height':self.cmra.height
            }}]},gameplayer.tcpCon)
     
gameplayer = GamePlayer()  

#hur dur gets free port? auto selected by OS
def get_free_tcp_port():
    print('getting free port')
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port

port = get_free_tcp_port()
st_url = "http://localhost:"+str(port)
print('link to HTML5 GUI:',st_url)

#cleint mode rendering
def js_direct(rq):
    js_snd(rq['data'])

def getDrawAbles(rq):
    js_snd(game.getDrawAbles())
    
def sckt_sendToOtherSocket(jsn_desu,clnt):
    #print('socket to socket')
    jsn_desu = jsnOjb(jsn_desu)
    jsn_desu = jsnStr(jsn_desu)
    clnt.sendall(str.encode(jsn_desu+'[[the_end]]'))

#websocket handler desu
@socketio.on('message')
def handleMessage(jsn):
    join_room('g')
    response = []
    for rq in jsn['data']:        
        fxn = getFxn(rq['do'])   
        rs = None
        try:
            rs = fxn(rq) #procDo(rq)
        except Exception as ex:
            print(ex)
            traceback.print_tb(ex.__traceback__)
            
        if(rs != None):#check for nulls senpai
            if(isinstance(rs, list)):                
                response.extend(rs)
            else:
                response.append(rs)
    #print(response) <- this shit creates lag desu SVG lag senpai
    if len(response) != 0:
        #print('response has content')
        js_snd(response)

#send to html5 front end
def js_snd(rsp):    
    socketio.emit('message',jsnOjb(rsp))
    
#ensures standard json object formatting
def jsnOjb(rsp):
    if isinstance(rsp,dict):
        if 'do' in rsp.keys():
            rsp = {'data':[rsp]}
    elif isinstance(rsp,list):
        rsp = {'data':rsp}
    return rsp

#ensure that json is in prop format and 
#is a made into a strin
def jsnStr(rsp):
    if not isinstance(rsp, str):
        return json.dumps(jsnOjb(rsp))  
    else:
        return rsp

def makeNewGame(rq):
    global game
    
    if(rq['data']['map'] == 'hell'):
        game = classDesu.Map_hell.Map_hell()
    elif(rq['data']['map'] == 'cem'):
        game = classDesu.Map_cem.Map_cem()
    elif(rq['data']['map'] == 'grass'):
        game = classDesu.Map_grassy.Map_grassy()
    elif(rq['data']['map'] == 'storm'):
        game = classDesu.Map_storm.Map_storm()
    elif(rq['data']['map'] == 'war'):
        game = classDesu.Map_warfield.Map_warfield()
    elif(rq['data']['map'] == 'snow'):
        game = classDesu.Map_snow.Map_snow()    
    elif(rq['data']['map'] == 'sea'):
        game = classDesu.Map_sea.Map_sea()
    elif(rq['data']['map'] == 'moon'):
        game = classDesu.Map_moon.Map_moon() 

#development purposes game environment
def makeNewDevGame(rq):
    global game    
    makeNewGame(rq)   
    game.addCharacter('Jon MingX 1','miming')
    game.addCharacter('Jon MingX 2','archer')
    game.addCharacter('Jon MingX 3','assassin')    
    game.addCharacter('Jon MingX 4','crusader')
    game.addCharacter('Jon MingX 5','dancer')    
    game.addCharacter('Jon MingX 6','lordKnight')    
    game.addCharacter('Jon MingX 7','sniper')    
    game.addCharacter('Jon MingX 8','stalker')  
    game.addCharacter('Jon MingX 9','santa')  
    game.current = game.actors[0]
    game.pausegame = True
    game.gamestarted = True
    #game.timerLeft = 0
    
makeNewDevGame({'data':{'map':'hell'}})
    
#actual running anf deploying of web app desu
if __name__ == '__main__':
    threading.Timer(1.25, lambda: webbrowser.open(st_url)).start()
    socketio.run(app,port=port)