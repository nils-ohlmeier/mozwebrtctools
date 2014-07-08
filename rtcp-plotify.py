#!/usr/bin/env python
import argparse, re, datetime, sys

in_stats_section = False

re_stats     = re.compile(r'.* STATS \(([0-9:\-\.TZ]*).*')
re_in_audio  = re.compile(r'.* (inbound_rtp_audio_[0-9]):')
re_in_video  = re.compile(r'.* (inbound_rtp_video_[0-9]):')
re_out_audio = re.compile(r'.* (outbound_rtp_audio_[0-9]):')
re_out_video = re.compile(r'.* (outbound_rtp_video_[0-9]):')
re_empty     = re.compile(r'^steeplechase INFO  \| $')

re_b_recv    = re.compile(r'.* bytesReceived: ([0-9]*)')
re_j         = re.compile(r'.* jitter: ([0-9\.]*)')
re_p_lost    = re.compile(r'.* packetsLost: ([0-9]*)')
re_p_recv    = re.compile(r'.* packetsReceived: ([0-9]*)')
re_b_sent    = re.compile(r'.* bytesSent: ([0-9]*)')
re_p_sent    = re.compile(r'.* packetsSent: ([0-9]*)')

stream_name = None
file_name = None
timestamp = None
rtcp_report = {}
plot = True

parser = argparse.ArgumentParser(description="Parse mochitest RTCP stats and send them to plotify")
parser.add_argument('logfile', type=str, help='the log file to parse')
parser.add_argument('-l', '--second-log', type=str, help='the second log file to parse')
parser.add_argument('-n', '--no-plot', action='store_false', help='do not plot on plotify')
parser.add_argument('-u', '--username', type=str, help='the username for plotify')
parser.add_argument('-p', '--password', type=str, help='the password for plotify')
args = parser.parse_args()

plot = args.no_plot

if (plot):
  import plotly.plotly as py
  from plotly.graph_objs import *
  if ((args.username is None) or (args.password is None)):
    print "error: missing username or password to use plotify"
    parser.print_help()
    sys.exit()
  py.sign_in(args.username, args.password)

stats = []

def update_stream_status(fn, sn):
  global stream_name
  stream_name = sn
  global file_name
  if (fn.rfind('.') != -1):
    fn = fn[:fn.rfind('.')]
  file_name = fn

def add_value(value_name, value):
  n = file_name + "-" + stream_name + "-" + value_name
  #print n
  rtcp_report[n] = value

def commit_report():
  global rtcp_report
  #print rtcp_report
  t = (timestamp, rtcp_report)
  stats.append(t)
  rtcp_report = {}

filenames = []
filenames.append(args.logfile)
if args.second_log:
  filenames.append(args.second_log)

for fn in filenames:
  f = open(fn)
  l = f.readline();
  while(l):
    m = re_stats.match(l)
    if m:
      in_stats_section = True
      ts = m.group(1)
      timestamp = datetime.datetime.strptime(ts.replace('Z', '')[:len(ts)-5], '%Y-%m-%dT%H:%M:%S')
    if in_stats_section:
      m = re_empty.match(l)
      if m:
        commit_report()
        in_stats_section = False
      m = re_in_audio.match(l)
      if m:
        update_stream_status(fn, m.group(1))
      m = re_in_video.match(l)
      if m:
        update_stream_status(fn, m.group(1))
      m = re_out_audio.match(l)
      if m:
        update_stream_status(fn, m.group(1))
      m = re_out_video.match(l)
      if m:
        update_stream_status(fn, m.group(1))
      m = re_b_recv.match(l)
      if m:
        add_value('bytes-received', m.group(1))
      #m = re_j.match(l)
      #if m:
      #  add_value('jitter', m.group(1))
      m = re_p_lost.match(l)
      if m:
        add_value('packets-lost', m.group(1))
      m = re_p_recv.match(l)
      if m:
        add_value('packets-received', m.group(1))
      m = re_b_sent.match(l)
      if m:
        add_value('bytes-send', m.group(1))
      m = re_p_sent.match(l)
      if m:
        add_value('packets-send', m.group(1))
    l = f.readline()

#print stats

traces = {}
for s in stats:
  r, d = s
  for key in d:
    traces[key] = {'x': [], 'y': []}
#print traces
for i in xrange(1, len(stats)):
  timestamp, vdict = stats[i]
  prev_t, prev_d = stats[i-1]
  for key in vdict:
    if not prev_d.has_key(key):
      continue
    traces[key]['x'].append(timestamp)
    d = int(vdict[key]) - int(prev_d[key])
    if (key.find('video') != -1) and (key.find('bytes') != -1):
      d = d/1000
    traces[key]['y'].append(d)

print traces.keys()

if (plot):
  a = []
  audio_a =[]
  video_a = []
  other_a = []
  for key in traces:
    if (key.find('audio') != -1) and (key.find('bytes') != -1):
      a.append(Scatter(x=traces[key]['x'], y=traces[key]['y'], mode='markers', name=key, yaxis='y2'))
    elif (key.find('video') != -1) and (key.find('bytes') != -1):
      a.append(Scatter(x=traces[key]['x'], y=traces[key]['y'], mode='markers', name=key, yaxis='y2'))
    else:
      a.append(Scatter(x=traces[key]['x'], y=traces[key]['y'], mode='markers', name=key))

  d = Data(a)
  l = Layout(title='Two Y axis', yaxis={'title': 'yaxis one'}, yaxis2=YAxis(title='yaxis two', side='right', overlaying='y'))

  fig = Figure(data=d, layout=l)

  plot_url = py.plot(fig, filename=filenames[0])
