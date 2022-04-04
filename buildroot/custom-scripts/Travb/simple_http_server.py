import sys
import platform
import os
from datetime import datetime
import time
from time import sleep
import http.server

from cpustat import *


HOST_NAME = '0.0.0.0' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8000

class GetCpuLoad(object):
    '''
    classdocs
    '''


    def __init__(self, percentage=True, sleeptime = 1):
        '''
        @parent class: GetCpuLoad
        @date: 04.12.2014
        @author: plagtag
        @info: 
        @param:
        @return: CPU load in percentage
        '''
        self.percentage = percentage
        self.cpustat = '/proc/stat'
        self.sep = ' ' 
        self.sleeptime = sleeptime

    def getcputime(self):
        '''
        http://stackoverflow.com/questions/23367857/accurate-calculation-of-cpu-usage-given-in-percentage-in-linux
        read in cpu information from file
        The meanings of the columns are as follows, from left to right:
            0cpuid: number of cpu
            1user: normal processes executing in user mode
            2nice: niced processes executing in user mode
            3system: processes executing in kernel mode
            4idle: twiddling thumbs
            5iowait: waiting for I/O to complete
            6irq: servicing interrupts
            7softirq: servicing softirqs

        #the formulas from htop 
             user    nice   system  idle      iowait irq   softirq  steal  guest  guest_nice
        cpu  74608   2520   24433   1117073   6176   4054  0        0      0      0


        Idle=idle+iowait
        NonIdle=user+nice+system+irq+softirq+steal
        Total=Idle+NonIdle # first line of file for all cpus

        CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)
        '''
        cpu_infos = {} #collect here the information
        with open(self.cpustat,'r') as f_stat:
            lines = [line.split(self.sep) for content in f_stat.readlines() for line in content.split('\n') if line.startswith('cpu')]

            #compute for every cpu
            for cpu_line in lines:
                if '' in cpu_line: cpu_line.remove('')#remove empty elements
                cpu_line = [cpu_line[0]]+[float(i) for i in cpu_line[1:]]#type casting
                cpu_id,user,nice,system,idle,iowait,irq,softrig,steal,guest,guest_nice = cpu_line

                Idle=idle+iowait
                NonIdle=user+nice+system+irq+softrig+steal

                Total=Idle+NonIdle
                #update dictionionary
                cpu_infos.update({cpu_id:{'total':Total,'idle':Idle}})
            return cpu_infos

    def getcpuload(self):
        '''
        CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)

        '''
        start = self.getcputime()
        #wait a second
        sleep(self.sleeptime)
        stop = self.getcputime()

        cpu_load = {}

        for cpu in start:
            Total = stop[cpu]['total']
            PrevTotal = start[cpu]['total']

            Idle = stop[cpu]['idle']
            PrevIdle = start[cpu]['idle']
            CPU_Percentage=((Total-PrevTotal)-(Idle-PrevIdle))/(Total-PrevTotal)*100
            cpu_load.update({cpu: CPU_Percentage})
        return cpu_load

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        cpuStats = GetCpuLoad()

        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write(b"<html><head><title>Title goes here.</title></head>")
        s.wfile.write(b"<body><marquee>This is a test.</marquee>")
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        # accessedPath = "<p>You accessed path: {}</p>".format(s.path)
        # s.wfile.write(accessedPath.encode())

        # Date Time
        dateWithTime = "<p>Data e Hora do Sistema: {}</p>".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        s.wfile.write(dateWithTime.encode())

        # Uptime
        #curUptime = "<p>Uptime do sistema (em segundos): {}</p>".format(int(os.popen('uptime -p').read()[:-1].split(" ")[1])*60)
        curUptime = "<p>Uptime do sistema (em segundos): {}</p>".format(cpuStats.getcputime())
        s.wfile.write(curUptime.encode())

        # Modelo CPU
        with open("/proc/cpuinfo") as f:
            content = f.readlines()
            f.close()
        cpuModel = "<p>Modelo do Processador e Velocidade:{}</p>".format(content[4].split(":")[1])
        s.wfile.write(cpuModel.encode())

        # Capacidade CPU
        cpuLoad = "<p>Capacidade ocupada do processador (%): {}</p>".format(cpuStats.getcpuload())
        s.wfile.write(cpuLoad.encode())

        # RAM
        with open("/proc/meminfo") as f:
            content = f.readlines()
            f.close()
        totalMem = int(content[0].split(" ")[-2])/1024
        usedMem = totalMem - int(content[1].split(" ")[-2])/1024
        curRAM = "<p>Quantidade de memoria RAM total e usada (MB): {}</p>".format("</br>Total: {}".format(totalMem) + "</br>Usada: {}".format(usedMem))
        s.wfile.write(curRAM.encode())

        # Versão do sistema
        sysVersion = "<p>Versao do Sistema: {}</p>".format(platform.system() + " " + platform.release() + " " + platform.version())
        s.wfile.write(sysVersion.encode())

        # Lista de processos
        processList = "</br>    "
        for dirname in os.listdir('/proc'):
            try:
                #print('/proc/{}/stat'.format(dirname))
                with open('/proc/{}/stat'.format(dirname)) as fd:
                    content = fd.read().split(" ")
                    curPID = content[0]
                    curPName = content[1]

                    processList = processList + "PID: " + curPID + " ---- Name: " + curPName + "</br>    "

                    fd.close()
            except Exception:
                continue
        #print(processList)

        processListHTML = "<p>Lista de processos em execucao (PID e nome): {}</p>".format(processList)
        s.wfile.write(processListHTML.encode())

        s.wfile.write(b"</body></html>") 


if __name__ == '__main__':
    server_class = http.server.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))

