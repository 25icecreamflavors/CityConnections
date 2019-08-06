# Install necessary libraries
# Use line below to install library, if it doesn't work
#!{sys.executable} -m pip install geopy
import sys
import requests
import csv
import geopy.distance
import numpy
import folium
from folium.plugins import MarkerCluster

# Creating dictionary of countires and their codes using our database
countries = {}
countries_keys = []
with open('CountryCodes.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    for row in reader:
        countries[row[1]] = row[0]
        countries_keys.append(row[1])
        
print("Please, enter the country name:")        

# Checking the correctness of user's input
InputCountry = str(input())
i = 0
while (i != 1):
    if InputCountry in countries.keys():
        i = 1
        InputCountry = "&country="+countries[InputCountry]
    elif (InputCountry == "c"):
        print(*countries_keys, sep=", ")
        print("\n")
        InputCountry = str(input())
    else:
        print("There is not such country, please, enter correct name.\
 If you would like to see the list of existing countries, enter 'c'.")
        InputCountry = str(input())

        
# Short names for parts of link
str1 = "http://api.geonames.org/searchJSON?&maxRows=1000"
str2 = "&featureClass=P&featureCodePPL&cities=cities15000&username=..." #Enter your username instead of ...


# First request
response = requests.get(str1+InputCountry+str2)
city = response.json()
m = city['totalResultsCount']
if (m == 1):
    print("There is " + str(m) + " city.")
else:
    print("There are " + str(m) + " cities.")
    
    
k1 = [] #List of cities and their coordinates 
if (m > 0):
    for p in city['geonames']:
        #print(p['toponymName'] + " " + p['lat'] + " " + p['lng'])
        k2 = []
        k2.extend([p['toponymName'], p['lat'], p['lng']])
        k1.append(k2)

        
# If there more than 1000 cities, send other requests
count = 1001
while (count < m) or (count < 5000):
    c = "&startRow=" + str(count)
    response = requests.get(str1+c+InputCountry+str2)
    city = response.json()
    for p in city['geonames']:
        #print(p['toponymName'] + " " + p['lat'] + " " + p['lng'])
        k2 = []
        k2.extend([p['toponymName'], float(p['lat']), float(p['lng'])])
        k1.append(k2)
    count = count + 1000

    
# Create a CSV file with cities names and their coordinates
city_index = {}
with open("output.csv", 'a', encoding='utf-8') as outcsv:   
    #configure writer to write standard CSV file
    writer = csv.writer(outcsv, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    index = 0
    for item in k1:
        #Write item to outcsv
        writer.writerow([item[0], item[1], item[2]])
        city_index[item[0]] = index
        index += 1
print("CSV file has been created.")


# Creating matrix of distances between cities and weighted graph
Graph = []
distances = numpy.zeros( (len(k1), len(k1)) )
for i in range(0, len(k1)):
    for j in range(i, len(k1)):
        coords_1 = (k1[i][1], k1[i][2])
        coords_2 = (k1[j][1], k1[j][2])
        total = geopy.distance.geodesic(coords_1, coords_2).km
        distances[i][j] = total
        distances[j][i] = total
        Graph.append([i, j, total])
print("Matrix of distances has been created.")


# Jarník's algorithm, Prim–Jarník algorithm, Prim–Dijkstra algorithm or the DJP algorithm
def PrimSpanningTree(V, G, DistanceMatrix):
    # Starting with zero vertex
    vertex = 0
    
    # Create empty arrays for algorithm
    MST = []
    edges = []
    visited = []
    minEdge = [None, None, float('inf')]
    
    # Repeating the algorithm until MST contains all vertices
    while len(MST) != V-1:
        # mark this vertex as visited
        visited.append(vertex)
        
        # Edges that may be possible for connection
        for e in range(0, V):
            if DistanceMatrix[vertex][e] != 0:
                edges.append([vertex, e, DistanceMatrix[vertex][e]])
        
        # Find edge with the smallest weight for a vertex that is not visited
        for e in range(0, len(edges)):
            if edges[e][2] < minEdge[2] and edges[e][1] not in visited:
                minEdge = edges[e]
        
        edges.remove(minEdge)
        MST.append(minEdge)
        
        # start at new vertex and reset min edge
        vertex = minEdge[1]
        minEdge = [None, None, float('inf')]
    return MST


# Kruskal's algorithm, V is number of vertices
def KruskalSpanningTree(V, Graph):
    # Sort edges in graph by their weigth
    Graph.sort(key = lambda x: x[2])
    result = []
    empty = set()
    
    # Create set for each vertice
    vertices = {}
    for i in range(0, V):
        vertices[i] = set([i])

    for edge in range(0, len(Graph)):
        begin = Graph[edge][0]
        end = Graph[edge][1]
        if (vertices[begin].intersection(vertices[end]) == empty):
            result.append([begin, end])
            temporary = vertices[begin].union(vertices[end])
            vertices[begin] = temporary
            vertices[end] = temporary
            for vertice in vertices[end]:
                vertices[vertice] = temporary
    return result


# Boruvka's way of solving problems
def Boruvka(distances):
    setMatrix = []
    allEdges = []
    for i in range(0, len(distances)):
        setMatrix.append([i])

    def combine(e):
        e0 = -1
        e1 = -1
        for i in range(0, len(setMatrix)):
            if e[0] in setMatrix[i]:
                e0 = i
            if e[1] in setMatrix[i]:
                e1 = i
        setMatrix[e0] += setMatrix[e1]
        del setMatrix[e1]

    while (len(setMatrix) > 1):
        edges = []
        for component in setMatrix:
            m = [9999999, [0, 0]]
            for vertex in component:
                for i in range(0, len(distances[0])):
                    if i not in component and distances[vertex][i] != 0:
                        if (m[0] > distances[vertex][i]):
                            m[0] = distances[vertex][i]
                            m[1] = [vertex, i]
            if (m[1][0] > m[1][1]):
                m[1][0], m[1][1] = m[1][1], m[1][0]
            if (m[1] not in edges):
                edges.append(m[1])
        for e in edges:
            combine(e)
            allEdges.append(e)
    return allEdges


#Create map
the_map = folium.Map(location=[k1[0][1], k1[0][2]], zoom_start = 5)

#Create Cluster
marker_cluster = MarkerCluster().add_to(the_map)
for i in range(len(k1)):
    folium.Marker(location=[k1[i][1], k1[i][2]], popup=k1[i][0], icon=folium.Icon(color = 'gray')).add_to(marker_cluster)

# Connect all cities using minimum spanning tree
# Chose one of your preference
print("Choose algorithm for connecting cities:")
print("1 - Jarník's algorithm, Prim–Jarník algorithm, Prim–Dijkstra algorithm.")
print("2 - Kruskal's algorithm")
print("3 - Boruvka's algorithm ")
print("Enter the number of algorhitm. If input is incorrect, program will choose the second one.")
AlgorithmChoice = input()
if (AlgorithmChoice == "1"):
    roads = PrimSpanningTree(len(k1), Graph, distances)
elif (AlgorithmChoice == "3"):
    roads = Boruvka(distances)
else:
    roads = KruskalSpanningTree(len(k1), Graph)

# City connection
for i in range(0, len(roads)):
    coords_1 = (float(k1[roads[i][0]][1]), float(k1[roads[i][0]][2]))
    coords_2 = (float(k1[roads[i][1]][1]), float(k1[roads[i][1]][2]))
    line = [coords_1, coords_2]
    dist = str("%.2f" % distances[roads[i][0]][roads[i][1]]) + " km"
    folium.PolyLine(locations=line, weight=5, color='green', tooltip=dist).add_to(the_map)

# Add layer control
folium.TileLayer('openstreetmap').add_to(the_map)
folium.TileLayer('stamenterrain').add_to(the_map)
folium.TileLayer('CartoDB dark_matter').add_to(the_map)
folium.LayerControl().add_to(the_map)

# Save map
the_map.save("map.html")
print("Map has been saved.")
