import subprocess
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import re
from datetime import datetime, timedelta
from time import sleep
from tqdm import trange
import argparse
from scipy.interpolate import make_interp_spline, BSpline
import numpy as np
from brokenaxes import brokenaxes

def ping(host, timeout=None):
	command = ['ping', "-n", "1", host]
	if timeout is not None:
		command = command + ["-w", str(timeout)]

	result = subprocess.run(command, capture_output=True)
	output = str(result.stdout).split("\\r\\n")[2]
	data = re.search("(?!time=)\d+(?=ms)", output)

	if data is not None:
		data = int(data.group())
	else:
		data = 0

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

	for i in trange(num_pings, desc="Pinging", ascii=" ░▒▓█"):
		data[i] = ping(hostname, wait_time)
		sleep(wait_time * .001)

	end_time = datetime.now()
	td = end_time - start_time

	minV = None
	maxV = None
	avgV = 0
	miss = 0

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
		minV = 0

	if maxV == None:
		maxV = 0

	begin_range = 0
	ranges = []

	in_zeroes = False

	timestep = td.total_seconds() / num_pings

	for i, el in enumerate(data):
		if el == 0 and not in_zeroes and begin_range != i-1:
			ranges.append( (begin_range * timestep,  (i-1) * timestep) )
			# begin_range = i
			in_zeroes = True
		elif in_zeroes and el != 0:
			begin_range = i
			in_zeroes = False

	if in_zeroes == False:
		ranges.append( (begin_range * timestep, num_pings * timestep) )

	avgV = round(avgV/(num_pings-miss), ndigits=2)

	print("Finished")
	print(f"Min Ping time: {minV}ms    Max Ping time: {maxV}ms    Average Ping time: {avgV}ms    Missed Pings: {miss} [{round(miss/num_pings*100, ndigits=2)}%]    Total Time: {round(td.total_seconds(), ndigits=2)}s")

	try:
		if (args.show_graph):
			# sps1, sps2 = GridSpec(2,1)

			T = [i * td.total_seconds() / num_pings for i in range(num_pings)]
			# x_axis = np.linspace(0, T[-1], num_pings*10)

			# spl = make_interp_spline(T, data, k=3)
			# power_smooth = spl(x_axis)

			# bax = brokenaxes(xlims=ranges, subplot_spec=sps1)
			# # bax.plot(x_axis, power_smooth, 'b-')
			# bax.plot(T, data, 'b-')
			# bax.set_ylabel('Ping time (ms)')
			# bax.set_xlabel('Time (s)')

			# bax = brokenaxes(xlims=((0, T[-1]),), subplot_spec=sps2)
			# bax.plot(T,data, 'ro-')
			# bax.set_ylabel('Ping time (ms)')
			# bax.set_xlabel('Time (s)')

			plt.bar(T, data, width=timestep)
			plt.ylabel('Ping time (ms)')
			plt.xlabel('Time (s)')
			plt.axis(xmin=0-timestep/2, xmax=T[-1]+timestep/2)
			plt.show()
	except:
		print(ranges)
		raise
