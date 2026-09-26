from duongdep.export import gmaps_url, select_waypoints, to_gpx
from duongdep.graph import Edge, Graph
from duongdep.score import score_edge


def test_select_waypoints_caps():
    coords = [(21.0 + i * 0.001, 105.8) for i in range(50)]
    wps = select_waypoints(coords, 9)
    assert len(wps) <= 9
    assert coords[0] not in wps and coords[-1] not in wps


def test_gmaps_url_shape():
    coords = [(21.0, 105.8), (21.01, 105.81), (21.02, 105.82)]
    url = gmaps_url(coords, platform="app")
    assert url.startswith("https://www.google.com/maps/dir/?")
    assert "api=1" in url
    assert "origin=21.000000%2C105.800000" in url
    assert "destination=21.020000%2C105.820000" in url
    assert "travelmode=driving" in url


def test_gmaps_mobile_limits_waypoints():
    coords = [(21.0 + i * 0.001, 105.8 + i * 0.001) for i in range(30)]
    url = gmaps_url(coords, platform="mobile")
    wp = url.split("waypoints=")[1].split("&")[0] if "waypoints=" in url else ""
    assert len(wp.split("%7C")) <= 3


def test_gpx_contains_points():
    gpx = to_gpx([(21.0, 105.8), (21.01, 105.81)])
    assert "<trkpt lat=" in gpx
    assert "105.800000" in gpx


def test_score_prefers_big_road():
    small = Edge(
        id=0, u=1, v=2, way_id=1, length_m=100, highway="service",
        width_proxy_m=3.0, geometry=[[21.0, 105.8], [21.0, 105.81]],
    )
    big = Edge(
        id=1, u=1, v=2, way_id=2, length_m=100, highway="primary",
        surface="asphalt", width_proxy_m=12.0, geometry=[[21.0, 105.8], [21.0, 105.81]],
    )
    score_edge(small, "car")
    score_edge(big, "car")
    assert big.score > small.score


def test_graph_roundtrip(tmp_path):
    g = Graph()
    g.nodes = {1: (21.0, 105.8), 2: (21.001, 105.801)}
    g.edges = [Edge(id=0, u=1, v=2, way_id=9, length_m=150, highway="residential",
                    geometry=[[21.0, 105.8], [21.001, 105.801]])]
    p = tmp_path / "g.json"
    g.save(p)
    g2 = Graph.load(p)
    assert g2.nodes == g.nodes
    assert g2.edges[0].highway == "residential"
    assert g2.adj[1][0][0] == 2
