import subprocess
import matplotlib.pyplot as plt
import re
from datetime import datetime, timedelta
from time import sleep
from tqdm import trange
import argparse

def ping(host, timeout=None):
	'''Send a single ping to host
	Timeout can be any positive integer or None
	'''

	if not isinstance(timeout, int) and timeout is not None:
		raise TypeError(f"Timeout not integer or None")
	
	command = ['ping', "-n", "1", host] #construct command args
	if timeout is not None: #add wait time if specified
		command = command + ["-w", str(timeout)]

	result = subprocess.run(command, capture_output=True) #run the command and return output to result
	output = str(result.stdout).split("\\r\\n")[2] #split result on newlines, and get 3rd line (line with results)
	data = re.search("(?!time=)\d+(?=ms)", output) #extract ping time from result

	if data is not None: #if ping has not failed
		data = int(data.group())
	else:
		data = 0 #0 is used to denote a failed ping (as it is impossible to have 0ms ping to any host)

	return data


if __name__ == '__main__':

	#set up parser
	parser = argparse.ArgumentParser(description='Automated ping program to detect downtime.')

	parser.add_argument('-hostname', '-x', default="8.8.8.8", required=False,
		help='Hostname for the pings to be sent to.')

	parser.add_argument('-num_pings', '-n', type=int, default=50, required=False,
		help='Number of pings to be sent')

	parser.add_argument('-wait_time', '-w', type=int, default=150, required=False,
		help='Amount of time in milliseconds to wait between each ping.')

	parser.add_argument('-s', dest='show_graph', action='store_true',
		help='Whether to print the output graph')
	
	#processing
	args = parser.parse_args()

	hostname = str(args.hostname)
	num_pings = args.num_pings
	wait_time = args.wait_time
	data = [None] * num_pings
	start_time = datetime.now()

	for i in trange(num_pings, desc="Pinging", ascii=" ░▒▓█"): #print progress bar
		data[i] = ping(hostname, wait_time)
		sleep(wait_time * .001) #sleep for the same length as the maximum ping wait time to avoid overlapping pings

	end_time = datetime.now()
	td = end_time - start_time

	minV = None #minimum ping time (excluding missed pings)
	maxV = None #maximum ping time (excluding missed pings)
	avgV = 0 #average ping time (doubles as cumulative ping time temporarily)
	miss = 0 #number of missed pings

	for i in data:
		if i != 0:
			if minV == None:
				minV = i
			elif i < minV:
				minV = i

			if maxV == None:
				maxV = i
			elif i > maxV:
				maxV = i

			avgV += i

		else:
			miss += 1

	if minV == None:
		minV = 0 #default minimum value if all pings missed

	if maxV == None:
		maxV = 0 #default maximum value if all pings missed

	timestep = td.total_seconds() / num_pings #time per ping (for graphing)

	avgV = round(avgV/(num_pings-miss), ndigits=2) #find average ping of successful pings

	print("Finished")
	print(f"Min Ping time: {minV}ms    Max Ping time: {maxV}ms    Average Ping time: {avgV}ms    Missed Pings: {miss} [{round(miss/num_pings*100, ndigits=2)}%]    Total Time: {round(td.total_seconds(), ndigits=2)}s")

	if (args.show_graph):
		#show bar graph of ping response time versus time
		T = [i * td.total_seconds() / num_pings for i in range(num_pings)] #construct X axis
		plt.bar(T, data, width=timestep)
		plt.ylabel('Ping time (ms)')
		plt.xlabel('Time (s)')
		plt.axis(xmin=0-timestep/2, xmax=T[-1]+timestep/2) #extend graph slightly left and right to avoid cutting off edge-most bars
		plt.show()
