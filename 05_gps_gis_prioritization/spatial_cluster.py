import math
import uuid


class SpatialClusterManager:

    def __init__(self, distance_threshold_m=50):

        self.distance_threshold_m = distance_threshold_m
        self.clusters = []

    def haversine_distance(
        self,
        lat1,
        lon1,
        lat2,
        lon2
    ):

        R = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = (
            math.sin(dphi / 2) ** 2
            +
            math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dlambda / 2) ** 2
        )

        return (
            2
            * R
            * math.atan2(
                math.sqrt(a),
                math.sqrt(1 - a)
            )
        )

    def add_event(self, event):

        latitude = event.get("latitude")
        longitude = event.get("longitude")
        event_type = event.get("event_type")

        if latitude is None or longitude is None:
            return event

        # Find an existing nearby cluster
        for cluster in self.clusters:

            if cluster["event_type"] != event_type:
                continue

            distance = self.haversine_distance(
                latitude,
                longitude,
                cluster["latitude"],
                cluster["longitude"]
            )

            if distance <= self.distance_threshold_m:

                cluster["detection_count"] += 1

                bus_id = event.get("bus_id")

                if bus_id and bus_id not in cluster["buses"]:
                    cluster["buses"].append(bus_id)

                # Update cluster location
                cluster["latitude"] = round(
                    (
                        cluster["latitude"]
                        + latitude
                    ) / 2,
                    6
                )

                cluster["longitude"] = round(
                    (
                        cluster["longitude"]
                        + longitude
                    ) / 2,
                    6
                )

                event["cluster"] = {
                    "cluster_id": cluster["cluster_id"],
                    "detection_count":
                        cluster["detection_count"],
                    "bus_count":
                        len(cluster["buses"]),
                    "buses":
                        cluster["buses"]
                }

                return event

        # No nearby cluster found
        cluster_id = (
            "CLUSTER-"
            + str(uuid.uuid4())[:8]
        )

        new_cluster = {
            "cluster_id": cluster_id,
            "event_type": event_type,
            "latitude": latitude,
            "longitude": longitude,
            "detection_count": 1,
            "buses": []
        }

        bus_id = event.get("bus_id")

        if bus_id:
            new_cluster["buses"].append(bus_id)

        self.clusters.append(new_cluster)

        event["cluster"] = {
            "cluster_id": cluster_id,
            "detection_count": 1,
            "bus_count":
                len(new_cluster["buses"]),
            "buses":
                new_cluster["buses"]
        }

        return event