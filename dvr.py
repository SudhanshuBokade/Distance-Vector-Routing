#sys is for chcking arguments
#time is for maintaining intervals
#threading for mutitthreadng
#Queue for maintaining a shared queue
#copy for facility of deep copying
import sys
import time
import copy
import threading
from queue import Queue

#updating the queue of each router after 2s
def update_queue(router,shared_info,node_info):
    for n in router['neighbour']:
        # acquiring queue lock so that 2 threads don't overwrite the data
        queue_lock=shared_info[n][1]
        temp={}
        queue_lock.acquire()
        #Putting the dvr table in the neighbours of this thread
        for key, value in router['DVR'].items():
            temp[key] = value
        shared_info[n][0].put((node_info,copy.deepcopy(temp)))
        queue_lock.release()
    queue = shared_info[node_info][0]
    # Loop untill all the neighbouring routers have sent the updated table
    while queue.qsize()!=len(router['neighbour']):
        continue


# Function to update the table using Bellman Ford Algortihm
#this function continue till the point no nodes has any information to share
def Bellman_Ford(router,shared_info,node_info):
    queue = shared_info[node_info][0]
    newTable = copy.deepcopy(router['DVR'])
    # iter_countating over all the items of the queue
    while not queue.empty():
        nn,tables = queue.get()
        src = node_info
        for dest,value in newTable.items():
            cost1 = value[0]
            cost2 = tables[dest][0]
            if cost2 != float('inf') and cost2 + newTable[nn][0] < cost1:
                newCost, newHop = cost2 + router['DVR'][nn][0], router['DVR'][nn][1]
                newTable[dest] = (newCost, newHop)
    changed = {}
    # Now, we update the value and keep track of all the links where a change occured
    for dest,value in newTable.items():
        if router['DVR'][dest][0]!=value[0] or router['DVR'][dest][1]!=value[1]:
            changed[dest]=value
        router['DVR'][dest] = value
    return changed


def task(router,shared_info,id,node):
    # We now share table with neighbours and update table (neighbours.length > queue..size)
    i = 0
    while i<4:
        i+=1
        update_queue(router,shared_info,node)
        changed = Bellman_Ford(router,shared_info,node)

        # print new table
        totalNodes = 0
        s=''
        s += "\tROUTER: {rname}\n".format(rname=node)
        s += "Destination\tCost\tNext Router\n"
        for dest,value in router['DVR'].items():
            if dest in changed.keys():
                s = s + ' *  '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
            else:
                s = s + '    '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
            totalNodes += 1
        s += '\n'

        # checking if all threads have appended the new table and printing
        shared_info['lock'].acquire()
        shared_info['finalString'][id] = s
        shared_info['counter'].append(id)
        if(len(shared_info['counter']) == totalNodes):
            print('<----------------------------------Iteration {iter_count}----------------------------------\n'.format(iter_count=i))
            for s in shared_info['finalString']:
                print(s)
            shared_info['finalString'] = [0]*totalNodes
            shared_info['counter']=[]
        shared_info['lock'].release()
        time.sleep(2)
        # loop the threads untill all have complete the current iter_countation
        while True:
            shared_info['lock'].acquire()
            if id not in shared_info['counter']:
                 shared_info['lock'].release()
                 break
            shared_info['lock'].release()
        while id in shared_info['counter']:
            continue


#_print function prints the beginning condition of router
def _print(router,nlist):
    s='----------------------------------Begin----------------------------------\n'
    for node_info in nlist:
        s += "\tROUTER: {rname}\n".format(rname=node_info)
        s += "Destination\tCost\tNext Router\n"
        for dest,value in router[node_info]['DVR'].items():
            s = s + '    '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
        s += '\n'
    print(s)
# shared_info(common for all routers) dictionary having keys: {node_info, counter, lock,finalString} for storing shared information.
# The key node_info consists of the queue for each node where the updated tables are sent after each iteration amd also has a key lock.
shared_info={}
# reading the file
file_name=sys.argv[1]
file = open(file_name,'r')
Lines = file.readlines()
count=0
node_count=0
nlist=''
# Router dictionary having keys as node names for storing router information.
# node_info is a subsequent dictionary with keys: neighbour and DVR
router = {}
#Extracting the routers information from the lines of inputfile 
for l in Lines:
    s=l.strip()
    if s=='EOF':
        break
    if count==0:
        node_count=int(s)
        count=1
    elif count==1:
        nlist=s.split(' ')
        for node_info in nlist:
            shared_info[node_info]=[Queue(maxsize=node_count),threading.Lock()]
            router[node_info]={}
            router[node_info]['neighbour'] = []
            router[node_info]['DVR'] = {}
            for n in nlist:
                router[node_info]['DVR'][n]=(float('inf'),'NA')
            router[node_info]['DVR'][node_info]=(0,node_info)
        count=2
    else:
        source,destination,cost=s.split() 
        cost = float(cost)
        router[source]['DVR'][destination] = (cost,destination)
        router[destination]['DVR'][source] = (cost,source)
        router[source]['neighbour'].append(destination)
        router[destination]['neighbour'].append(source)
threads = []
shared_info['counter']= []
shared_info['lock'] = threading.Lock()
shared_info['finalString'] = [0]*node_count
_print(router,nlist)
for id,node in enumerate(nlist):
    th = threading.Thread(target=task, args=(router[node],shared_info,id,node))
    threads.append(th)
    th.start()
for th in threads:
    th.join()