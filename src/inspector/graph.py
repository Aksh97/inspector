import sys
import json
import re
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, OrderedDict


def to_alphanum(key):
    def convert(text):
        return int(text) if text.isdigit() else text

    def split(s):
        return [convert(c) for c in re.split('([0-9]+)', key(s))]
    return split


def autolabel(rects):
    # attach some text labels
    for rect in rects:
        height = rect.get_height()
        plt.text(rect.get_x()+rect.get_width()/2.,
                 height * 0.5,
                 '%.2f' % height,
                 ha='center',
                 va='bottom',
                 rotation="vertical")

PATTERNS = ('-', '+', 'x', '\\', '*', 'o', 'O', '.')
COLORS = ('b', 'g', 'r', 'c', 'm', 'y',)


def mean(v):
    if len(v) < 4:
        return np.std(v)
    v_ = v.copy()
    v_.remove(max(v_))
    v_.remove(min(v_))
    return np.mean(v_)


def std(v):
    if len(v) < 4:
        return np.std(v)
    v_ = v.copy()
    v_.remove(max(v_))
    v_.remove(min(v_))
    return np.std(v_)


def generate_graph1(log):
    def constructor():
        return defaultdict(OrderedDict)
    per_thread = defaultdict(constructor)
    for bench, per_lib in sorted(json.load(open(log)).items()):
        name, threads = bench.split("-", 1)
        for lib, data in per_lib.items():
            if lib == "threads":
                continue
            per_thread[int(threads)][lib][bench] = data

    bar_width = 0.40
    opacity = 0.4

    plt.figure(figsize=(10, 8))

    for thread, benchmarks in per_thread.items():
        bench_names = benchmarks["pthread"].keys()
        bench_names = map(lambda n: n.split("-", 1)[0], bench_names)
        pthread_values = []
        for v in benchmarks["pthread"].values():
            pthread_values.append(mean(v["times"]))
        del benchmarks["pthread"]

        i = 0
        for lib, per_lib in benchmarks.items():

            normalized_values = []
            std_values = []
            for v, w in zip(per_lib.values(), pthread_values):
                normalized_values.append(mean(v["times"]) / w)
                std_values.append(std(v["times"]))
            index = np.arange(0, len(normalized_values) * 2, 2)
            rect = plt.bar(index + bar_width * (i + 0.5),
                           normalized_values,
                           bar_width,
                           yerr=std_values,
                           color=COLORS[i],
                           alpha=opacity,
                           label=lib,
                           hatch=PATTERNS[i])
            #autolabel(rect)
            i += 1
            index += 0
        plt.xlabel('Benchmarks')
        plt.ylabel('Overhead')
        plt.title(name, y=1.00)
        plt.suptitle("Times by benchmarks and libraries for %d threads" %
                     thread,
                     y=1.00)
        plt.xticks(index + bar_width,
                   [n for n in bench_names],
                   rotation=50)
        plt.legend(loc='best')
        plt.grid()

        plt.tight_layout()
        plt.savefig("benchmarks-%d.pdf" % thread)
        plt.clf()


def generate_graph2(log):
    def constructor():
        return defaultdict(OrderedDict)
    per_lib = defaultdict(constructor)
    json_data = json.load(open(log))
    bench_names = set()
    sort = sorted(json_data.items(),
                  key=to_alphanum(lambda pair: pair[0]),
                  reverse=False)
    for bench, per_bench in sort:
        name, threads = bench.split("-", 1)
        bench_names.add(name)
        for lib, data in per_bench.items():
            if lib != "threads":
                per_lib[lib][int(threads)][bench] = data

    bar_width = 0.40
    opacity = 0.4

    pthread = per_lib["pthread"]
    del per_lib["pthread"]

    for lib, per_thread in per_lib.items():
        i = 0
        for thread, data in sorted(per_thread.items()):
            pthread_values = []
            for v in pthread[thread].values():
                pthread_values.append(mean(v["times"]))

            normalized_values = []
            std_values = []
            for v, w in zip(data.values(), pthread_values):
                normalized_values.append(mean(v["times"]) / w)
                std_values.append(std(v["times"]))
            index = np.arange(0, len(normalized_values) * 2, 2)
            rect = plt.bar(index + bar_width * (i + 0.5),
                           normalized_values,
                           bar_width,
                           yerr=std_values,
                           color=COLORS[i],
                           alpha=opacity,
                           label=thread,
                           hatch=PATTERNS[i])
            #autolabel(rect)
            i += 1
            index += 0
        plt.xlabel('Benchmarks')
        plt.ylabel('Overhead')
        plt.title(name, y=1)
        plt.suptitle("Times by benchmarks and threads for %s" % lib, y=1)
        plt.xticks(index + bar_width * 2,
                   sorted(bench_names),
                   rotation=60)
        plt.legend(loc='best')
        plt.grid()

        plt.savefig("benchmarks-%s.pdf" % lib)
        plt.tight_layout()
        plt.clf()


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        die("USAGE: %s log.json" % sys.argv[0])
    generate_graph1(sys.argv[1])
    generate_graph2(sys.argv[1])

if __name__ == "__main__":
    main()
