from cgi import test
from http import client
from optparse import Values
from pickle import FALSE, TRUE
from select import select
import string
import sys
import getopt
import ipaddress
from turtle import width
from unittest import result
import ping3
import os
import requests
import urllib3
from datetime import date, datetime
import subprocess
import speedtest
from docxtpl import *
from docx.shared import Mm
import sqlite3

urllib3.disable_warnings()

class bcolors:
    OK = '\033[92m' #GREEN
    WARNING = '\033[93m' #YELLOW
    FAIL = '\033[91m' #RED
    RESET = '\033[0m' #RESET COLOR

ddj = datetime.now()

########################  UTILITAIRE  ###############################

def parseFile(filepath, *ip):
    file = open(filepath, 'r')
    Lines = file.readlines()
    result_dict = {}
    for line in Lines:
        if ip:
            if len(line.strip().split(" ")) > 1:
                result_dict[line.strip().split(" ")[0]] = line.strip().split("/")[1]
            else:
                result_dict[line.strip().split(" ")[0]] = " "
        else: 
            if len(line.strip().split(" ")) > 1:
                result_dict[line.strip().split(" ")[0]] = line.strip().split(" ")[1]
            else:
                result_dict[line.strip().split(" ")[0]] = " "
    return result_dict

#fonction permettant de créer la base de donnée du client 
def base_de_donne(nomClient): 
        bd = './data/db/'+str(nomClient)+'.db'
        con = sqlite3.connect(bd)
        cur = con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS TEST(
                id INTEGER PRIMARY KEY AUTOINCREMENT, resultat TEXT, 
                statut TEXT,date Datetime2
                )''')
#fonction permettant le stokage des information sur les test dans la base de données client 
def insertion_base(nomClient, resultat,date): 
        statut = str(input("entrer test post ou pre: "))
        assert type(nomClient) == str
        nomBase = nomClient.lower()
        bd = './data/db/'+str(nomBase)+'.db'
        con = sqlite3.connect(bd)
        cur = con.cursor()
        ordre = "INSERT INTO TEST (resultat, statut, date) VALUES (?,?,?)"
        values = (resultat, statut,date)
        cur.execute(ordre,values)
        con.commit()
#fonction permattant de selection un test a partir de l'id de la base de données
def select_one(nomClient,id):
    bd = './data/db/'+str(nomClient)+'.db'
    con = sqlite3.connect(bd)
    cur = con.cursor()
    ordre = "SELECT * FROM TEST where id = ?"
    cur.execute(ordre,id)
    selected = cur.fetchall()
    return selected

#fonction permetant l'affichage des test pre et post réalisé et stock en mémoire
def show(nomClient,statut):
    bd = './data/db/'+str(nomClient)+'.db'
    con = sqlite3.connect(bd)
    cur = con.cursor()
    if statut == 'post':
        cur.execute("SELECT id,date FROM TEST WHERE statut like 'post'")
        result = cur.fetchall()
        print(bcolors.WARNING +"============ TEST POST ============" + bcolors.RESET)
    else:
        cur.execute("SELECT id,date FROM TEST WHERE statut like 'pre'")
        result = cur.fetchall()
        print(bcolors.WARNING +"============ TEST PRE ============" + bcolors.RESET)
    for row in result:
        print('ID : ', row[0],'  |  ', 'DATE : ', row[1])
        print(bcolors.WARNING +"=============================" + bcolors.RESET)

#fonction permettant la convertion en tableau des résultat stocké en chaine de caractére
def parse_retour_bd(selected):
    converti = list(list(selected))[0]
    return eval(converti[1])

#fonction permettant affiche les différence entre 2 tests
def delta(resultat_pre, resultat_post):
    delta = []
    for i in range(0,len(resultat_post)):
        delta_tmp = []
        for j in range(0,len(resultat_post[i])):
            e_pre = resultat_pre[i][j]
            e_post = resultat_post[i][j]
            if (e_post.get('result') != e_pre.get('result')):
                if i == 0: 
                    delta_tmp.append({'typeTest': e_post.get('typeTest'),'url': e_post.get('url'), 'port': 'HTTP/HTTPS', 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
                elif i == 1: 
                    delta_tmp.append({'typeTest': 'NC', 'ip': e_post.get('ip'), 'port': e_post.get('port'), 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
                elif i == 2:
                    delta_tmp.append({'typeTest': 'Ping','desc': e_post.get('desc'), 'ip': e_post.get('ip'), 'port': 'ICMP', 'result':  'avant '+ e_pre.get('result') + ' ---> aprés ' + e_post.get('result')})
        delta.append(delta_tmp)
    return delta


########################  TEST  ###############################
def test_ping(ips):
    result_ip = [] #variable de synthèse des test 
    assert type(ips) == dict
    print(bcolors.WARNING +"============ Network connectivity tests (ping) ============" + bcolors.RESET)
    for ip in ips.keys():
        response = ping3.ping(str(ip))
        if response == None:
            print(bcolors.FAIL +"Ping "+ ip + " ... NOK" + bcolors.RESET)
            result_ip.append({'typeTest': 'Ping','desc': ips[ip], 'ip': ip, 'port': 'ICMP', 'result': 'NOK'})
        else:
            print(bcolors.OK +"Ping "+ ip + " ... OK" + bcolors.RESET)
            result_ip.append({'typeTest': 'Ping','desc': ips[ip], 'ip': ip, 'port': 'ICMP', 'result': 'OK'})
    return result_ip

def test_urls(urls):
    result_url = [] #variable de synthèse des test 
    assert type(urls) == dict
    print(bcolors.WARNING +"============ URL HTTP/HTTPS tests (requests) ============" + bcolors.RESET)
    for url in urls:
        try:
            response = requests.get(url, verify=False)
        except: 
            print(bcolors.FAIL + url + " - Connection failed" + bcolors.RESET)
            if "http" in url: 
                result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result':  'NOK'})
        
            else:
                result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result':'NOK'})
        else:
            if response.status_code == 200:
                print(bcolors.OK + url + " - Status code : " + str(response.status_code) + " response size : " + str(sys.getsizeof(response.content)*0.001) + " ko" + bcolors.RESET)
                if "http" in url: 
                    result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result': 'OK'})
                else:
                    result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTPPS', 'result': 'OK'})
            elif response.status_code == 401:
                print(bcolors.WARNING + url + " - Status code : " + str(response.status_code) + " response size : " + str(sys.getsizeof(response.content)*0.001) + " ko" + bcolors.RESET)
                if "http" in url: 
                    result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result': 'NOK'})
                else:
                    result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result': 'NOK'})
            else:
                print(bcolors.FAIL + url + " - Status code : " + str(response.status_code) + " response size : " + str(sys.getsizeof(response.content)*0.001) + " ko" + bcolors.RESET)
                if "http" in url: 
                    result_url.append({'typeTest': 'URL','url': url, 'port': 'HTTP/HTTPS', 'result': 'NOK'})
                else:
                    result_url.append({'typeTest': 'URL ' + urls[url],'url': url, 'port': 'HTTP/HTTPS', 'result': 'NOK'})
    return result_url

def test_apps(apps):
    result_app = [] #variable de synthèse des test 
    print(bcolors.WARNING +"============ Apps availability tests (nc) ============" + bcolors.RESET)
    for app in apps:
        text_ipPort = app.split(":")
        out = subprocess.getoutput("ncat -vv -z -w3 "+app.split(":")[0]+" "+app.split(":")[1])
        if ("Connected" in out):
            print(bcolors.OK + apps.get(app)+" ... OK" + bcolors.RESET)
            result_app.append({'typeTest': 'NC','ip': text_ipPort[0], 'port': text_ipPort[1], 'result': 'OK'})
        else:
            print(bcolors.FAIL + apps.get(app)+" ... NOK" + bcolors.RESET)
            result_app.append({'typeTest': 'NC', 'ip': text_ipPort[0], 'port': text_ipPort[1], 'result': 'NOK'})
    return result_app

########################  RAPPORT  ###############################
#fonction permettant l'utilisation de jinja pour l'insertion dans le rapport
def generation_rapport(client,projet,resultat_pre,resultat_post,nombre_equipement,equipement,redacteur,diff):
    assert type(resultat_post) == list
    assert type(resultat_pre) == list
    assert type(client) == str
    image = [] 
    rapport = DocxTemplate("template.docx")
    #données
    col_equipement = ['Modèle','Hostname', 'Numéro de série (S/N)', 'Adresse MAC', 'Nombre de ports utilisés','Résultat (OK/NOK)']
    col_ip = ['Type de test','Description', 'IP', 'Port','Résultat (OK/NOK)']
    col_url = ['Type de test','URL', 'Port','Résultat (OK/NOK)']
    col_app = ['Type de test','IP', 'Port','Résultat (OK/NOK)']
    for i in range(0, nombre_equipement): 
        photo = './data/'+client.lower()+'/' + equipement[i].get('hostname')+'.jpg'
        image.append({'image': InlineImage(rapport, photo, height=Mm(60))})
    day = ddj.day
    month = ddj.month
    year = ddj.year 
    #tag template
    context = dict()
    context['client'] = client
    context['projet'] = projet
    context['day'] = day
    context['month'] = month
    context['year'] = year
    context['col_eq'] = col_equipement
    context['col_ip'] = col_ip
    context['col_url'] = col_url
    context['col_app'] = col_app
    context['image'] = image
    context['prenom_r'] = redacteur[1]
    context['nom_r'] = redacteur[0]
    context['fonction'] = redacteur[2]
    context['modele'] = equipement[0]['modele']
    context['ligne_equip'] = equipement
    context['ligne_ip_pre'] = resultat_pre[2]
    context['ligne_url_pre'] = resultat_pre[0]
    context['ligne_app_pre'] = resultat_pre[1]
    context['ligne_ip_post'] = resultat_post[2]
    context['ligne_url_post'] = resultat_post[0]
    context['ligne_app_post'] = resultat_post[1]
    context['ligne_ip_dif'] = diff[2]
    context['ligne_url_dif'] = diff[0]
    context['ligne_app_dif'] = diff[1]
    #generation du rapport
    rapport.render(context)
    rapportClient = "./data/"+ client + "/rapport-"+ client + ".docx"
    rapport.save(rapportClient)



def main(argv):
    history = True
    resultat = []
    try:
        opts, args = getopt.getopt(argv,"hrwu:a:i:n",["rapport=", "web=","urls=","apps=","ips=","nosave="])
    except getopt.GetoptError:
        print('recette.py -r -w -u <urlsfile> -a <appsfile> -i <ipsfile>')
        sys.exit(2)
    startTime = datetime.now()
    print("Starting tests at "+str(startTime))
    for opt, arg in opts:
        if opt == '-h':
            print('recette.py -r -w -u <urlsfile> -a <appsfile> -i <ipsfile>')
            sys.exit()
        elif opt in ("-r", "--rapport") or opt == '-r': #option pour génération du rapport
            nomClient = str(input ("entrer le nom du client: "))
            nomProjet = str(input ("entrer le nom du Projet: "))
            history = False
            nomBase = nomClient.lower()
            redacteur =[]
            equipement = []
            nombre_equipement = int(input("entrer le nombre d'équipement installé: "))
            for i in range (nombre_equipement):
                modele = input("entrer le modèle de l'équipement: ")
                hostname = input("entrer le hostname: ")
                numero_serie = input("entrer le numéro de série: ")
                adresse_mac = input("entrer l'adresse mac: ")
                nombre_de_port = input("enter le nombre de port utilisé: ")
                re = str(input("entrer le resultat (OK/NOK) :"))
                while ((re != "OK" or re != "NOK") != True):
                    re = str(input("entrer le resultat (OK/NOK) :"))
                equipement.append({'modele': modele, 'hostname': hostname, 'numero_serie': numero_serie, 'adresse_mac': adresse_mac, 'nombre_port': nombre_de_port, 're': re })
            prenom = input("Entrer le nom du redacteur du rapport: ")
            nom = input("Entrer le prenom du redacteur du rapport: ")
            fonction = input("Entrer la fonction du redacteur du rapport: ")
            redacteur.append(nom)
            redacteur.append(prenom)
            redacteur.append(fonction)
            id_pre = input("choisir l'id pre du pour le rapport: ")
            resultat_pre = parse_retour_bd(select_one(nomClient,id_pre))
            id_post = input("choisir l'id post du pour le rapport: ")
            resultat_post = parse_retour_bd(select_one(nomClient,id_post))
            dif = delta(resultat_pre,resultat_post)
            generation_rapport(nomClient,nomProjet,resultat_pre,resultat_post, nombre_equipement, equipement,redacteur,dif)
        elif opt in ("-w", "--web") or opt == '-w': #option pour génération du rapport
            os.system("flask run")
        elif opt in ("-u", "--urls"): #option pour test url
            URLS_TO_TEST = parseFile(arg)
            resultat.append(test_urls(URLS_TO_TEST))
        elif opt in ("-i", "--ips"): #option pour les test ip
            IPS_TO_PING = parseFile(arg,True)
            resultat.append(test_ping(IPS_TO_PING))
        elif opt in ("-a", "--apps"): #option pour les test d'applications
            APPS_TO_TEST = parseFile(arg)
            resultat.append(test_apps(APPS_TO_TEST))
        elif opt in ("-n", "--nosave"): #option pour la sauvegarde dans la base de donnée
            history = False
            
    stokage = str(resultat)
    if history: #sauvegarde dans la base de donnée
        nomClient = str(input ("entrer le nom du client: "))
        nomBase = nomClient.lower()
        base_de_donne(nomBase)
        insertion_base(nomBase, stokage,startTime)
    print("End of tests at "+str(datetime.now()))

if __name__ == "__main__":
   main(sys.argv[1:])