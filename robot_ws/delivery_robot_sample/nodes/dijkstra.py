#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# このノードは navigation スタックへの操作を経路ファイルから行います
# これはノードではない


import os
import math
import rospy
import json
import time
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Log
import itertools


class Planner():
    def __init__(self):
        

        self.__vertex_list = []
        self.__vertex_list.append(Vertex(0,  0.0000,  0.0000, is_destination=True))
        self.__vertex_list.append(Vertex(1,  0.8229,  0.0967))
        self.__vertex_list.append(Vertex(2,  2.3392,  0.1538, is_destination=True))
        self.__vertex_list.append(Vertex(3,  3.1411,  0.2866))
        self.__vertex_list.append(Vertex(4,  4.4300,  0.4448))
        self.__vertex_list.append(Vertex(5,  4.4891,  1.3000))
        self.__vertex_list.append(Vertex(6,  5.5000,  1.3000, is_destination=True))
        self.__vertex_list.append(Vertex(7,  3.1020,  1.3000))
        self.__vertex_list.append(Vertex(8,  3.1660,  1.9090, is_destination=True))
        self.__vertex_list.append(Vertex(9,  3.1033,  2.0947))
        self.__vertex_list.append(Vertex(10, 1.9200,  2.0740))
        self.__vertex_list.append(Vertex(11, 1.3677,  2.6072))
        self.__vertex_list.append(Vertex(12, 1.0188,  2.3708, is_destination=True))
        self.__vertex_list.append(Vertex(13, 0.9226,  2.2745))
        self.__vertex_list.append(Vertex(14, -0.2187, 1.5910))
        self.__vertex_list.append(Vertex(15, 0.0932,  0.8834))
        self.__vertex_list.append(Vertex(16, 0.9781,  1.0678))
        self.__vertex_list.append(Vertex(17, 0.8400,  1.3642))
        self.__vertex_list.append(Vertex(18, 2.0236,  1.3482))
        self.__destination_num = len([x for x in self.__vertex_list if x.get_is_destination()])

        Edge(self.__vertex_list[0], self.__vertex_list[1])
        Edge(self.__vertex_list[1], self.__vertex_list[2])
        Edge(self.__vertex_list[2], self.__vertex_list[3])
        Edge(self.__vertex_list[3], self.__vertex_list[4])
        Edge(self.__vertex_list[4], self.__vertex_list[5])
        Edge(self.__vertex_list[5], self.__vertex_list[6])
        Edge(self.__vertex_list[3], self.__vertex_list[7])
        Edge(self.__vertex_list[5], self.__vertex_list[7])
        Edge(self.__vertex_list[7], self.__vertex_list[8])
        Edge(self.__vertex_list[8], self.__vertex_list[9])
        Edge(self.__vertex_list[9], self.__vertex_list[10])
        Edge(self.__vertex_list[10], self.__vertex_list[11])
        Edge(self.__vertex_list[11], self.__vertex_list[12])
        Edge(self.__vertex_list[12], self.__vertex_list[13])
        Edge(self.__vertex_list[13], self.__vertex_list[14])
        Edge(self.__vertex_list[14], self.__vertex_list[15])
        Edge(self.__vertex_list[1], self.__vertex_list[15])
        Edge(self.__vertex_list[15], self.__vertex_list[16])
        Edge(self.__vertex_list[16], self.__vertex_list[17])
        Edge(self.__vertex_list[16], self.__vertex_list[18])
        Edge(self.__vertex_list[13], self.__vertex_list[17])
        Edge(self.__vertex_list[7], self.__vertex_list[18])
        self.__shortest_path_dict = {}

    def main(self):
        self.__calc_all_patterns()

    def __calc_all_patterns(self, start_vertex_id=0):
        destination_id_list = []
        start_vertex = None
        # 目的地となるvertex_idを取得する
        for vertex in self.__vertex_list:
            if vertex.get_is_destination():
                self.__dijkstra_planner(vertex)
                vertex_id = vertex.get_vertex_id()
                if vertex_id != start_vertex_id:
                    destination_id_list.append(vertex_id)
                else:
                    start_vertex = vertex
        # すべての巡回経路を算出
        all_patterns = map(list, itertools.permutations(destination_id_list))
        mini_cost = float("inf")
        mini_cost_path = None
        # 最小となる巡回経路を算出する
        for path in all_patterns:
            p = start_vertex_id
            tmp_cost = 0
            for c in path:
                key = "%d-%d" % (p, c)
                p = c
                tmp_cost += self.__shortest_path_dict[key]["cost"]
            if mini_cost > tmp_cost:
                mini_cost = tmp_cost
                mini_cost_path = path

        p = start_vertex_id
        full_path = [start_vertex]
        for c in mini_cost_path:
            key = "%d-%d" % (p, c)
            p = c
            half_path = self.__shortest_path_dict[key]["path"]
            if half_path[0].get_vertex_id() == c:
                half_path.reverse()
            full_path.extend(half_path[1:])
        print("Destination path: %s" % mini_cost_path)
        print("Full path: %s" % map(lambda x: x.get_vertex_id(), full_path))
        return full_path

    def __dijkstra_planner(self, start_vertex):

        # vertexごとのSTARTからの最小コスト
        min_dist_dict = {}
        min_dist_dict[start_vertex] = 0
        # vertexに最小コストで辿り着く場合の直前のノード
        prev_vertex_dict = {}
        prev_vertex_dict[start_vertex] = Vertex(None, None, None)
        queue = []
        # START vertex をキューにプッシュ
        queue.append(start_vertex)
        arrived_destination = []
        arrived_destination.append(start_vertex)

        while True:
            # 確定した vertex から遷移可能な vertex のうち
            # 最小コストと遷移先ノードを min_dist_dict と prev_node_dict に設定
            queue.sort(key=lambda v: min_dist_dict[v])
            vertex = queue.pop(0)

            # GOAL
            if vertex.get_is_destination():
                # goalノードには複数回行くことがあるのでリストとか作ってlength使う?
                if not vertex in arrived_destination:
                    path = []
                    tmp_vertex = vertex
                    while True:
                        path.append(tmp_vertex)
                        if tmp_vertex.get_vertex_id() == start_vertex.get_vertex_id():
                            break
                        tmp_vertex = prev_vertex_dict[tmp_vertex]
                    result = {
                        "cost": min_dist_dict[vertex],
                        "path": path
                    }
                    key = "%d-%d" % (path[0].get_vertex_id(), path[-1].get_vertex_id())
                    self.__shortest_path_dict[key] = result
                    key = "%d-%d" % (path[-1].get_vertex_id(), path[0].get_vertex_id())
                    self.__shortest_path_dict[key] = result
                    arrived_destination.append(vertex)
                    if(len(arrived_destination) >= self.__destination_num):
                        print("start_vertex %d" % start_vertex.get_vertex_id())
                        print("min_dist_dict %s" %  {key.get_vertex_id(): min_dist_dict[key] for key in min_dist_dict} )
                        print("prev_vertex_dict %s" % {key.get_vertex_id(): prev_vertex_dict[key].get_vertex_id() for key in prev_vertex_dict})
                        return

            prev_vertex = vertex
            # 確定したノードから遷移可能な vertex について
            # コストを計算し、キューに追加する
        
            # 直前に確定した vertex から遷移可能な edge について繰り返し
            for arrival_edge in prev_vertex.get_edge_list():
                # 遷移可能なvertexについて、直前に確定したvertexから遷移した場合のコストを計算
                tmp_d = min_dist_dict[prev_vertex] + arrival_edge.get_cost()
                arrival_vertex = arrival_edge.get_opposite_vertex(prev_vertex)
                # 過去に遷移先ノードの最小コストを計算済みかどうか
                if arrival_vertex in min_dist_dict.keys():
                    # 過去に計算していたSTARTからの最小コストより直前に確定したノードから遷移した場合の
			        # コストが小さかった場合，最小コストを更新
                    if tmp_d < min_dist_dict[arrival_vertex]:
                        min_dist_dict[arrival_vertex] = tmp_d
                        queue.append(arrival_vertex)
                        prev_vertex_dict[arrival_vertex] = prev_vertex
                else:
                    min_dist_dict[arrival_vertex] = tmp_d
                    queue.append(arrival_vertex)
                    prev_vertex_dict[arrival_vertex] = prev_vertex

class Vertex:
    def __init__(self, vertex_id, x, y, is_destination=False):
        self.__edge_list = []  # 
        self.__x = x
        self.__y = y
        self.__is_destination = is_destination
        self.__vertex_id = vertex_id
    
    def set_edge(self, edge):
        if edge in self.__edge_list:
            return
        self.__edge_list.append(edge)

    def get_position(self):
        return self.__x, self.__y

    def get_is_destination(self):
        return self.__is_destination
    
    def get_edge_list(self):
        return self.__edge_list
    
    def get_vertex_id(self):
        return self.__vertex_id

class Edge:
    def __init__(self, vertex_a, vertex_b):
        self.__vertex_list = [vertex_a, vertex_b]
        self.__cost = self.__calc_cost()
        vertex_a.set_edge(self)
        vertex_b.set_edge(self)

    def get_opposite_vertex(self, my_vertex):
        if not my_vertex in self.__vertex_list:
            return None
        for v in self.__vertex_list:
            if v is my_vertex:
                continue
            return v

    def __calc_cost(self):
        ax, ay = self.__vertex_list[0].get_position()
        bx, by = self.__vertex_list[1].get_position()
        return ((ax - bx)**2 + (ay - by)**2)**0.5

    def get_cost(self):
        return self.__cost

def main():
    planner = Planner()
    planner.main()


if __name__ == '__main__':
    main()