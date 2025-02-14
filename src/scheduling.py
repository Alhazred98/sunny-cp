'''
Module for computing and parallelizing the solvers schedule of SUNNY algorithm.
'''

import csv
from math import sqrt
from combinations import *

def get_neighbours(feat_vector, k, kb):
  """
  Returns a dictionary (inst_name, inst_info) of the k instances closer to the
  feat_vector in the knowledge base kb. If k <= 0, then k is set to the square
  root of the knowledge base size.
  """
  reader = csv.reader(open(kb, 'r'), delimiter = '|')
  infos = {}
  feat_vectors = {}
  distances = []
  n = 0
  for row in reader:
    n += 1
    inst = row[0]
    d = euclidean_distance(feat_vector, list(map(float, row[1][1 : -1].split(','))))
    distances.append((d, inst))
    infos[inst] = row[2]
  sorted_dist = distances.sort(key = lambda x : x[0])
  if k <= 0:
    k = int(round(sqrt(n)))
  return dict((inst, infos[inst]) for (d, inst) in distances[0 : k])

def euclidean_distance(fv1, fv2):
  """
  Computes the Euclidean distance between two feature vectors fv1 and fv2.
  """
  assert len(fv1) == len(fv2)
  distance = 0.0
  for i in range(0, len(fv1)):
    d = fv1[i] - fv2[i]
    distance += d * d
  return sqrt(distance)

def sunny_csp(neighbours, k, timeout, pfolio, backup, min_size):
  """
  Given the neighborhood of a given CSP and the runtime infos, returns the
  corresponding SUNNY schedule.
  """
  solved = {}
  times  = {}
  for solver in pfolio:
    solved[solver] = set([])
    times[solver]  = 0.0
  for inst, item in list(neighbours.items()):
    item = eval(item)
    for solver in pfolio:
      time = item[solver]['time']
      if time < timeout:
        solved[solver].add(inst)
      times[solver] += time
  max_solved = 0
  min_time = float('+inf')
  best_pfolio = []
  m = len(pfolio)
  # Select the best sub-portfolio. min_size is the minimum cardinality.
  for i in range(min_size, m + 1):
    old_pfolio = best_pfolio
    for j in range(0, binom(m, i)):
      solved_instances = set([])
      solving_time = 0
      # get the (j + 1)-th subset of cardinality i
      sub_pfolio = get_subset(j, i, pfolio)
      for solver in sub_pfolio:
        solved_instances.update(solved[solver])
        solving_time += times[solver]
      num_solved = len(solved_instances)
      if num_solved >  max_solved or \
        (num_solved == max_solved and solving_time < min_time):
          min_time = solving_time
          max_solved = num_solved
          best_pfolio = sub_pfolio
    if old_pfolio == best_pfolio:
      break
  # n is the number of instances solved by each solver plus the instances
  # that no solver can solver.
  n = sum([len(solved[s]) for s in best_pfolio]) + (k - max_solved)
  schedule = {}
  # Compute the schedule and sort it by number of solved instances.
  for solver in best_pfolio:
    ns = len(solved[solver])
    if ns == 0 or round(timeout / n * ns) == 0:
      continue
    schedule[solver] = timeout / n * ns
  tot_time = sum(schedule.values())
  # Allocate to the backup solver the (eventual) remaining time.
  if round(tot_time) < timeout:
    if backup in list(schedule.keys()):
      schedule[backup] += timeout - tot_time
    else:
      schedule[backup]  = timeout - tot_time
  sorted_schedule = sorted(
    list(schedule.items()),
    key = lambda x: times[x[0]]
  )
  assert(round(sum(t for (s, t) in sorted_schedule)) <= timeout)
  return sorted_schedule

def sunny_cop(neighbours, k, timeout, pfolio, backup, min_size):
  """
  Given the neighborhood of a given COP and the runtime infos, returns the
  corresponding SUNNY schedule.
  """
  scores = {}
  times  = {}
  areas  = {}

  for solver in pfolio:
    scores[solver] = []
    times[solver] = 0.0
    areas[solver] = 0.0
  for inst, item in list(neighbours.items()):
    item = eval(item)
    for solver in pfolio:
      scores[solver].append(item[solver]['score'])
      times[solver] += item[solver]['time']
      areas[solver] += item[solver]['area']
  max_score = 0
  min_time = float('+inf')
  min_area = float('+inf')
  best_pfolio = []
  # Select the best sub-portfolio.
  m = len(pfolio)
  for i in range(min_size, m + 1):
    old_pfolio = best_pfolio
    for j in range(0, binom(m, i)):
      score = 0
      time = 0
      area = 0
      # get the (j + 1)-th subset of cardinality i
      sub_pfolio = get_subset(j, i, pfolio)
      port_scores = dict([
        (s, l) for s, l in list(scores.items()) if s in sub_pfolio
      ])
      for h in range(0, k):
        score += max([inst[h] for inst in list(port_scores.values())])
      time = sum([times[solver] for solver in sub_pfolio])
      area = sum([areas[solver] for solver in sub_pfolio])
      if score >  max_score or \
        (score == max_score and time < min_time) or \
        (score == max_score and time == min_time and area < min_area):
          min_time  = time
          min_area  = area
          max_score = score
          best_pfolio = sub_pfolio
    if old_pfolio == best_pfolio:
      break
  # n is the number of instances solved by each solver plus the instances
  # that no solver can solver.
  n = sum([sum(scores[s]) for s in best_pfolio]) + (k - max_score)
  schedule = {}
  # compute the schedule and sort it by number of solved instances.
  for solver in best_pfolio:
    ns = sum(scores[solver])
    if ns == 0 or round(timeout / n * ns) == 0:
      continue
    schedule[solver] = timeout / n * ns
  tot_time = sum(schedule.values())
  if round(tot_time) < timeout:
    if backup in list(schedule.keys()):
      schedule[backup] += timeout - tot_time
    else:
      schedule[backup]  = timeout - tot_time
  sorted_schedule = sorted(
    [(s, t) for (s, t) in list(schedule.items())],
    key = lambda x: times[x[0]]
  )
  return sorted_schedule

def parallelize(seq_sched, cores, timeout):
  """
  Given a sequential schedule of n > cores solvers, returns its parallelization.
  """
  assert len(seq_sched) > cores
  sort_sched = sorted(seq_sched, key = lambda x: x[1], reverse = True)
  par_sched = [(s, float('+inf')) for (s, _) in sort_sched[:cores - 1]]
  seq_sched = [x for x in seq_sched if x[0] not in list(dict(par_sched).keys())]
  seq_time = sum(t for (_, t) in seq_sched)
  for (s, t) in seq_sched:
    par_sched.append((s, t * timeout / seq_time))
  assert round(sum(t for (s, t) in par_sched[cores - 1:]), 5) == timeout
  return par_sched
