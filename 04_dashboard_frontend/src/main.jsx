import React, {
  useEffect,
  useMemo,
  useState
} from "react";

import {
  createRoot
} from "react-dom/client";

import "leaflet/dist/leaflet.css";
import "./styles.css";

import {
  Activity,
  Ambulance,
  AlertTriangle,
  ArrowUpRight,
  Bell,
  BusFront,
  Car,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Crosshair,
  Gauge,
  Layers3,
  MapPin,
  Moon,
  Radio,
  Route,
  Search,
  ShieldAlert,
  Siren,
  Signal,
  Sparkles,
  Sun,
  TriangleAlert,
  Wifi,
  X,
  Zap
} from "lucide-react";

import {
  MapContainer,
  Marker,
  Polyline,
  TileLayer,
  Popup,
  useMap
} from "react-leaflet";

import L from "leaflet";


// ============================================================
// CONFIG
// ============================================================

const API_URL =
  "http://127.0.0.1:8000/api";

const CENTER = [
  12.9716,
  77.5946
];


// ============================================================
// DEMO BUS DATA
// ============================================================

const BUSES = [
  {
    id: "BMTC-042",
    route: "500D",
    lat: 12.9592,
    lng: 77.7011,
    state: "Sensing",
    events: 8,
    speed: 31
  },
  {
    id: "BMTC-117",
    route: "335E",
    lat: 12.9178,
    lng: 77.6233,
    state: "Sensing",
    events: 11,
    speed: 18
  },
  {
    id: "BMTC-088",
    route: "201R",
    lat: 12.9431,
    lng: 77.6218,
    state: "Sensing",
    events: 5,
    speed: 23
  },
  {
    id: "BMTC-031",
    route: "276",
    lat: 13.0281,
    lng: 77.5199,
    state: "Sensing",
    events: 4,
    speed: 36
  },
  {
    id: "BMTC-204",
    route: "KIA-9",
    lat: 12.9662,
    lng: 77.6033,
    state: "Standby",
    events: 2,
    speed: 0
  }
];


// ============================================================
// DEMO ROUTE
// ============================================================

const ROUTE = [
  [12.9178, 77.6233],
  [12.9431, 77.6218],
  [12.9592, 77.7011],
  [12.9662, 77.6033],
  [13.0281, 77.5199]
];


// ============================================================
// EMERGENCY CORRIDOR
// ============================================================

const DEFAULT_EMERGENCY_CORRIDOR = [
  [12.9716, 77.5946],
  [12.9688, 77.5995],
  [12.9640, 77.6065],
  [12.9570, 77.6140],
  [12.9490, 77.6210]
];


// ============================================================
// ICONS
// ============================================================

const ICONS = {
  road: TriangleAlert,
  traffic: Car,
  infrastructure: Signal,
  unsafe: ShieldAlert,
  emergency: Ambulance
};


// ============================================================
// MAP EVENT MARKER
// ============================================================

function createEventIcon(event) {

  let color = "#f6b73c";

  if (
    event.severity === "High"
  ) {
    color = "#ff5d73";
  }

  if (
    event.severity === "Critical"
  ) {
    color = "#ff3030";
  }

  if (
    event.category === "traffic"
  ) {
    color = "#f6b73c";
  }

  if (
    event.category === "infrastructure"
  ) {
    color = "#59d7ff";
  }

  if (
    event.category === "unsafe"
  ) {
    color = "#b58cff";
  }

  if (
    event.category === "emergency"
  ) {
    color = "#ff3030";
  }

  return L.divIcon({
    className:
      "codyssey-event-marker",

    html: `
      <div
        class="event-marker-dot"
        style="
          --marker-color:${color};
          --marker-shadow:${color}55;
        "
      >
        <span></span>
      </div>
    `,

    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });
}


// ============================================================
// BUS MARKER
// ============================================================

function createBusIcon() {

  return L.divIcon({
    className:
      "codyssey-bus-marker",

    html:
      `<div class="bus-marker-dot">🚌</div>`,

    iconSize: [28, 28],
    iconAnchor: [14, 14]
  });
}


// ============================================================
// EMERGENCY MARKER
// ============================================================

function createEmergencyIcon() {

  return L.divIcon({
    className:
      "codyssey-emergency-marker",

    html: `
      <div
        style="
          width:34px;
          height:34px;
          border-radius:50%;
          background:#ff3030;
          display:flex;
          align-items:center;
          justify-content:center;
          color:white;
          font-size:18px;
          border:3px solid white;
          box-shadow:
            0 0 0 6px #ff303044,
            0 0 25px #ff3030aa;
        "
      >
        🚑
      </div>
    `,

    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });
}


// ============================================================
// EVENT CONVERTER
// ============================================================

function convertBackendAlert(alert) {

  const eventType =
    alert.event_type ||
    "Unknown event";


  // ----------------------------------------------------------
  // CATEGORY
  // ----------------------------------------------------------

  let category = "road";

  if (
    eventType === "traffic"
  ) {
    category = "traffic";
  }

  else if (
    eventType === "road_infrastructure"
  ) {
    category = "infrastructure";
  }

  else if (
    eventType === "unsafe_behaviour"
  ) {
    category = "unsafe";
  }

  else if (
    eventType === "emergency"
  ) {
    category = "emergency";
  }

  else {
    category = "road";
  }


  // ----------------------------------------------------------
  // VALUES
  // ----------------------------------------------------------

  const confidence =
    Number(
      alert.confidence || 0
    );

  const priority =
    Number(
      alert.priority_score || 0
    );


  let severity =
    alert.severity ||
    "medium";

  severity =
    severity.charAt(0).toUpperCase() +
    severity.slice(1);


  // ----------------------------------------------------------
  // DISPLAY NAME
  // ----------------------------------------------------------

  let displayName =
    eventType
      .replaceAll("_", " ")
      .replace(
        /\b\w/g,
        c => c.toUpperCase()
      );


  if (
    eventType === "pothole"
  ) {
    displayName =
      "Pothole";
  }

  if (
    eventType === "road_damage"
  ) {
    displayName =
      "Road damage";
  }

  if (
    eventType ===
    "road_infrastructure"
  ) {
    displayName =
      "Road infrastructure";
  }

  if (
    eventType ===
    "unsafe_behaviour"
  ) {
    displayName =
      "Unsafe behaviour";
  }

  if (
    eventType === "traffic"
  ) {
    displayName =
      alert.class_name ===
      "congestion"
        ? "Traffic congestion"
        : "Traffic";
  }

  if (
    eventType === "emergency"
  ) {

    if (
      alert.class_name
    ) {

      const emergencyName =
        String(
          alert.class_name
        );

      displayName =
        emergencyName
          .replace(
            /\b\w/g,
            c =>
              c.toUpperCase()
          );

    } else {

      displayName =
        "Emergency vehicle";
    }
  }


  // ----------------------------------------------------------
  // LOCATION
  // ----------------------------------------------------------

  const latitude =
    Number(alert.latitude);

  const longitude =
    Number(alert.longitude);


  const hasLocation =
    Number.isFinite(latitude) &&
    Number.isFinite(longitude);


  return {

    id:
      alert.id
        ? `EVT-${String(
            alert.id
          ).padStart(4, "0")}`
        : `EVT-${Date.now()}`,

    type:
      displayName,

    category,

    severity,

    confidence,

    location:
      hasLocation
        ? `${latitude.toFixed(
            4
          )}, ${longitude.toFixed(
            4
          )}`
        : "Location unavailable",

    lat:
      hasLocation
        ? latitude
        : CENTER[0],

    lng:
      hasLocation
        ? longitude
        : CENTER[1],

    bus:
      alert.bus_id ||
      "Unknown bus",

    buses:
      Number(
        alert.buses ||
        alert.validation?.cross_bus_validation?.bus_count ||
        1
      ),

    time:
      alert.timestamp
        ? formatTime(
            alert.timestamp
          )
        : "Just now",

    status:
      priority >= 80
        ? "Verified"
        : "Review",

    impact:
      priority >= 80
        ? "High"
        : "Monitoring",

    priority,

    raw:
      alert
  };
}


// ============================================================
// TIME FORMATTER
// ============================================================

function formatTime(timestamp) {

  try {

    const date =
      new Date(timestamp);

    const seconds =
      Math.floor(
        (
          Date.now() -
          date.getTime()
        ) / 1000
      );


    if (
      seconds < 0
    ) {
      return "Just now";
    }


    if (
      seconds < 60
    ) {
      return `${seconds} sec ago`;
    }


    const minutes =
      Math.floor(
        seconds / 60
      );


    if (
      minutes < 60
    ) {
      return `${minutes} min ago`;
    }


    const hours =
      Math.floor(
        minutes / 60
      );

    return `${hours} hr ago`;

  }

  catch {

    return "Recently";
  }
}


// ============================================================
// MAP FLY
// ============================================================

function FlyTo({
  target
}) {

  const map =
    useMap();


  useEffect(() => {

    if (
      target
    ) {

      map.flyTo(
        target,
        13,
        {
          duration: 0.7
        }
      );
    }


    const handleRecenter =
      () => {

        map.flyTo(
          CENTER,
          12,
          {
            duration: 0.7
          }
        );
      };


    window.addEventListener(
      "codyssey-recenter",
      handleRecenter
    );


    return () => {

      window.removeEventListener(
        "codyssey-recenter",
        handleRecenter
      );
    };

  }, [
    target,
    map
  ]);


  return null;
}


// ============================================================
// BADGE
// ============================================================

function Badge({
  children,
  tone = "neutral"
}) {

  return (

    <span
      className={
        "badge " + tone
      }
    >
      {children}
    </span>
  );
}


// ============================================================
// STAT
// ============================================================

function Stat({
  icon: Icon,
  label,
  value,
  detail,
  tone = ""
}) {

  return (

    <div
      className={
        "stat-card " +
        tone
      }
    >

      <div className="stat-icon">
        <Icon size={18} />
      </div>


      <div className="stat-copy">

        <span>
          {label}
        </span>

        <strong>
          {value}
        </strong>

        <small>
          {detail}
        </small>

      </div>


      <ArrowUpRight
        size={16}
        className="stat-arrow"
      />

    </div>
  );
}


// ============================================================
// MAP
// ============================================================

function MapPanel({
  events,
  selected,
  setSelected,
  showBuses,
  emergencyEvent
}) {

  const emergencyPosition =
    emergencyEvent
      ? [
          emergencyEvent.lat,
          emergencyEvent.lng
        ]
      : null;


  const emergencyCorridor =
    emergencyEvent
      ? [
          emergencyPosition,
          ...DEFAULT_EMERGENCY_CORRIDOR
        ]
      : [];


  return (

    <div className="map-wrap">

      <MapContainer
        center={CENTER}
        zoom={12}
        zoomControl
        scrollWheelZoom
      >

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />


        {/* ----------------------------------------------------
            NORMAL SENSING ROUTE
        ---------------------------------------------------- */}

        <Polyline
          positions={ROUTE}
          pathOptions={{
            color: "#59d7ff",
            weight: 3,
            opacity: 0.7,
            dashArray: "8 8"
          }}
        />


        {/* ----------------------------------------------------
            EMERGENCY PRIORITY CORRIDOR
        ---------------------------------------------------- */}

        {emergencyEvent && (

          <Polyline
            positions={
              emergencyCorridor
            }
            pathOptions={{
              color: "#ff3030",
              weight: 7,
              opacity: 0.95,
              dashArray: "12 8"
            }}
          />

        )}


        {/* ----------------------------------------------------
            EVENT MARKERS
        ---------------------------------------------------- */}

        {events.map(
          event => (

            <Marker
              key={event.id}
              position={[
                event.lat,
                event.lng
              ]}
              icon={
                createEventIcon(
                  event
                )
              }
              eventHandlers={{
                click: () =>
                  setSelected(
                    event
                  )
              }}
            >

              <Popup>

                <div
                  style={{
                    minWidth:
                      "180px"
                  }}
                >

                  <strong
                    style={{
                      display:
                        "block",
                      fontSize:
                        "14px",
                      marginBottom:
                        "6px"
                    }}
                  >
                    {event.type}
                  </strong>


                  <div
                    style={{
                      fontSize:
                        "11px",
                      marginBottom:
                        "4px"
                    }}
                  >
                    📍{" "}
                    {event.location}
                  </div>


                  <div
                    style={{
                      fontSize:
                        "11px",
                      marginBottom:
                        "4px"
                    }}
                  >
                    🚌{" "}
                    {event.bus}
                  </div>


                  <div
                    style={{
                      fontSize:
                        "11px",
                      marginBottom:
                        "4px"
                    }}
                  >
                    Confidence:{" "}
                    {Math.round(
                      event.confidence *
                      100
                    )}
                    %
                  </div>


                  <div
                    style={{
                      fontSize:
                        "11px"
                    }}
                  >
                    Priority:{" "}
                    {event.priority}
                  </div>

                </div>

              </Popup>

            </Marker>

          )
        )}


        {/* ----------------------------------------------------
            EMERGENCY VEHICLE MARKER
        ---------------------------------------------------- */}

        {emergencyEvent && (

          <Marker
            position={[
              emergencyEvent.lat,
              emergencyEvent.lng
            ]}
            icon={
              createEmergencyIcon()
            }
          >

            <Popup>

              <div
                style={{
                  minWidth:
                    "200px"
                }}
              >

                <strong>
                  🚑{" "}
                  {emergencyEvent.type}
                </strong>

                <div
                  style={{
                    marginTop:
                      "8px",
                    fontSize:
                      "12px"
                  }}
                >
                  AI detected emergency
                  vehicle
                </div>

                <div
                  style={{
                    marginTop:
                      "5px",
                    fontSize:
                      "12px"
                  }}
                >
                  Confidence:{" "}
                  {Math.round(
                    emergencyEvent.confidence *
                    100
                  )}
                  %
                </div>

                <div
                  style={{
                    marginTop:
                      "5px",
                    fontSize:
                      "12px"
                  }}
                >
                  Priority:{" "}
                  {emergencyEvent.priority}
                </div>

              </div>

            </Popup>

          </Marker>

        )}


        {/* ----------------------------------------------------
            BUS MARKERS
        ---------------------------------------------------- */}

        {showBuses &&
          BUSES.map(
            bus => (

              <Marker
                key={bus.id}
                position={[
                  bus.lat,
                  bus.lng
                ]}
                icon={
                  createBusIcon()
                }
              >

                <Popup>

                  <div
                    style={{
                      minWidth:
                        "150px"
                    }}
                  >

                    <strong
                      style={{
                        display:
                          "block",
                        fontSize:
                          "13px",
                        marginBottom:
                          "5px"
                      }}
                    >
                      {bus.id}
                    </strong>


                    <div
                      style={{
                        fontSize:
                          "11px"
                      }}
                    >
                      Route:{" "}
                      {bus.route}
                    </div>


                    <div
                      style={{
                        fontSize:
                          "11px"
                      }}
                    >
                      Speed:{" "}
                      {bus.speed} km/h
                    </div>


                    <div
                      style={{
                        fontSize:
                          "11px"
                      }}
                    >
                      Events:{" "}
                      {bus.events}
                    </div>


                    <div
                      style={{
                        fontSize:
                          "11px"
                      }}
                    >
                      Status:{" "}
                      {bus.state}
                    </div>

                  </div>

                </Popup>

              </Marker>

            )
          )}


        <FlyTo
          target={
            selected
              ? [
                  selected.lat,
                  selected.lng
                ]
              : null
          }
        />

      </MapContainer>


      {/* ------------------------------------------------------
          MAP TITLE
      ------------------------------------------------------ */}

      <div
        className="map-overlay top-left"
      >

        <div className="map-title">

          <div>

            <span className="eyebrow">
              LIVE CITY VIEW
            </span>

            <h2>
              Urban sensing network
            </h2>

          </div>


          <Badge tone="live">

            <CircleDot
              size={10}
            />

            LIVE

          </Badge>

        </div>

      </div>


      {/* ------------------------------------------------------
          MAP CONTROLS
      ------------------------------------------------------ */}

      <div
        className="map-overlay top-right"
      >

        <button
          type="button"
          className="map-control"
        >

          <Layers3
            size={16}
          />

          Layers

        </button>


        <button
          type="button"
          className="map-control"
          onClick={() => {

            window.dispatchEvent(
              new CustomEvent(
                "codyssey-recenter"
              )
            );

          }}
        >

          <Crosshair
            size={16}
          />

          Recenter

        </button>

      </div>


      {/* ------------------------------------------------------
          MAP LEGEND
      ------------------------------------------------------ */}

      <div
        className="map-overlay bottom-left legend"
      >

        <div>
          <i className="dot high" />
          High priority
        </div>

        <div>
          <i className="dot medium" />
          Medium
        </div>

        <div>
          <i className="dot bus" />
          Active bus
        </div>

        <div>
          <i className="line-route" />
          Sensing corridor
        </div>

        {emergencyEvent && (

          <div>
            <i
              className="dot"
              style={{
                background:
                  "#ff3030"
              }}
            />
            Emergency corridor
          </div>

        )}

      </div>


      {/* ------------------------------------------------------
          SELECTED EVENT
      ------------------------------------------------------ */}

      {selected && (

        <div className="event-popover">

          <button
            type="button"
            onClick={() =>
              setSelected(
                null
              )
            }
          >
            <X size={15} />
          </button>


          <span className="eyebrow">
            {selected.id}
          </span>


          <h3>
            {selected.type}
          </h3>


          <p>

            <MapPin
              size={14}
            />

            {selected.location}

          </p>


          <div className="popover-grid">

            <div>

              <small>
                Confidence
              </small>

              <strong>
                {Math.round(
                  selected.confidence *
                  100
                )}
                %
              </strong>

            </div>


            <div>

              <small>
                Bus
              </small>

              <strong>
                {selected.bus}
              </strong>

            </div>


            <div>

              <small>
                Severity
              </small>

              <strong>
                {selected.severity}
              </strong>

            </div>


            <div>

              <small>
                Priority
              </small>

              <strong>
                {selected.priority}
              </strong>

            </div>

          </div>


          <Badge
            tone={
              selected.buses >= 2
                ? "verified"
                : "review"
            }
          >

            {selected.buses >= 2
              ? "CROSS-BUS VERIFIED"
              : "SINGLE BUS OBSERVATION"}

          </Badge>

        </div>

      )}

    </div>
  );
}


// ============================================================
// APP
// ============================================================

function App() {

  // ==========================================================
  // STATE
  // ==========================================================

  const [
    active,
    setActive
  ] = useState(
    "Command Center"
  );


  const [
    filter,
    setFilter
  ] = useState(
    "All"
  );


  const [
    selected,
    setSelected
  ] = useState(
    null
  );


  const [
    showBuses,
    setShowBuses
  ] = useState(
    true
  );


  const [
    dark,
    setDark
  ] = useState(
    true
  );


  const [
    alerts,
    setAlerts
  ] = useState(
    []
  );


  const [
    backendOnline,
    setBackendOnline
  ] = useState(
    false
  );


  const [
    loading,
    setLoading
  ] = useState(
    true
  );


  // ==========================================================
  // FETCH ALERTS
  // ==========================================================

  const fetchAlerts =
    async () => {

      try {

        const response =
          await fetch(
            `${API_URL}/alerts`
          );


        if (
          !response.ok
        ) {

          throw new Error(
            "Backend request failed"
          );
        }


        const data =
          await response.json();


        const backendAlerts =
          Array.isArray(data)
            ? data
            : (
                data.alerts ||
                []
              );


        const converted =
          backendAlerts
            .map(
              convertBackendAlert
            )
            .reverse();


        setAlerts(
          converted
        );


        setBackendOnline(
          true
        );


        setLoading(
          false
        );

      }

      catch (error) {

        console.error(
          "Backend connection error:",
          error
        );


        setBackendOnline(
          false
        );


        setLoading(
          false
        );

      }
    };


  // ==========================================================
  // LIVE POLLING
  // ==========================================================

  useEffect(() => {

    fetchAlerts();


    const interval =
      setInterval(
        fetchAlerts,
        2000
      );


    return () =>
      clearInterval(
        interval
      );

  }, []);


  // ==========================================================
  // FILTER
  // ==========================================================

  const filtered =
    useMemo(() => {

      if (
        filter === "All"
      ) {

        return alerts;
      }


      const mapping = {

        Road:
          "road",

        Traffic:
          "traffic",

        Infrastructure:
          "infrastructure",

        Unsafe:
          "unsafe"

      };


      return alerts.filter(
        event =>
          event.category ===
          mapping[filter]
      );

    }, [
      alerts,
      filter
    ]);


  // ==========================================================
  // AUTOMATIC EMERGENCY EVENT
  // ==========================================================
  //
  // IMPORTANT:
  //
  // There is NO setEmergency().
  //
  // Emergency state is derived directly
  // from the AI-generated backend alert.
  //
  // ==========================================================

  const emergencyEvent =
    useMemo(() => {

      return (
        alerts.find(
          event =>
            event.category ===
            "emergency"
        ) || null
      );

    }, [
      alerts
    ]);


  const emergency =
    Boolean(
      emergencyEvent
    );


  // ==========================================================
  // STATISTICS
  // ==========================================================

  const activeIncidents =
    alerts.length;


  const verifiedEvents =
    alerts.filter(
      event =>
        event.priority >=
        80
    ).length;


  const trafficEvents =
    alerts.filter(
      event =>
        event.category ===
        "traffic"
    ).length;


  const emergencyEvents =
    alerts.filter(
      event =>
        event.category ===
        "emergency"
    ).length;


  const averageConfidence =
    alerts.length
      ? Math.round(
          alerts.reduce(
            (
              sum,
              event
            ) =>
              sum +
              event.confidence,
            0
          ) /
          alerts.length *
          100
        )
      : 0;


  // ==========================================================
  // NAVIGATION
  // ==========================================================

  const nav = [

    [
      "Command Center",
      Activity
    ],

    [
      "City Map",
      MapPin
    ],

    [
      "Incidents",
      AlertTriangle
    ],

    [
      "Fleet",
      BusFront
    ],

    [
      "Emergency",
      Ambulance
    ],

    [
      "Analytics",
      Gauge
    ]

  ];


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div
      className={
        "app " +
        (
          dark
            ? "dark"
            : "light"
        )
      }
    >


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">


        <div className="brand">

          <div className="brand-mark">

            <Route
              size={23}
            />

          </div>


          <div>

            <strong>
              CODYSSEY
            </strong>

            <span>
              URBAN INTELLIGENCE
            </span>

          </div>

        </div>


        {/* SYSTEM STATUS */}

        <div className="system-state">

          <span className="pulse" />


          <div>

            <strong>

              {backendOnline
                ? "NETWORK ONLINE"
                : "BACKEND OFFLINE"}

            </strong>


            <small>

              {backendOnline
                ? "Edge fleet synchronized"
                : "Waiting for FastAPI"}

            </small>

          </div>


          <Wifi
            size={15}
          />

        </div>


        {/* NAV */}

        <nav>

          <span className="nav-label">
            OPERATIONS
          </span>


          {nav.map(
            ([label, Icon]) => (

              <button
                key={label}
                className={
                  "nav-item " +
                  (
                    active ===
                    label
                      ? "active"
                      : ""
                  )
                }
                onClick={() =>
                  setActive(
                    label
                  )
                }
              >

                <Icon
                  size={18}
                />


                <span>
                  {label}
                </span>


                {label ===
                  "Incidents" && (

                  <b>
                    {activeIncidents}
                  </b>

                )}


                {label ===
                  "Emergency" &&
                  emergency && (

                  <b>
                    1
                  </b>

                )}


                {active ===
                  label && (

                  <ChevronRight
                    size={15}
                    className={
                      "nav-chevron"
                    }
                  />

                )}

              </button>

            )
          )}

        </nav>


        {/* SIDEBAR BOTTOM */}

        <div className="sidebar-bottom">


          <div className="coverage">

            <div className="coverage-head">

              <span>
                City coverage
              </span>

              <strong>
                78%
              </strong>

            </div>


            <div className="progress">

              <i
                style={{
                  width:
                    "78%"
                }}
              />

            </div>


            <small>
              42 sensing buses active
            </small>

          </div>


          <div className="profile">

            <div className="avatar">
              CI
            </div>


            <div>

              <strong>
                CODYSSEY Ops
              </strong>

              <small>
                Administrator
              </small>

            </div>


            <ChevronRight
              size={15}
            />

          </div>

        </div>

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="main">


        {/* TOP BAR */}

        <header className="topbar">


          <div className="mobile-brand">

            <Route
              size={20}
            />

            CODYSSEY

          </div>


          <div className="crumbs">

            <span>
              OPERATIONS
            </span>


            <ChevronRight
              size={13}
            />


            <strong>
              {
                active.toUpperCase()
              }
            </strong>

          </div>


          <div className="top-actions">


            <div className="search">

              <Search
                size={16}
              />


              <input
                placeholder={
                  "Search events, buses, roads..."
                }
              />

            </div>


            <button
              className="icon-btn"
            >

              <Bell
                size={18}
              />

              <i />

            </button>


            <button
              className="icon-btn"
              onClick={() =>
                setDark(
                  !dark
                )
              }
            >

              {dark
                ? (
                  <Sun
                    size={18}
                  />
                )
                : (
                  <Moon
                    size={18}
                  />
                )}

            </button>

          </div>

        </header>


        <section className="content">


          {/* ==================================================
              HERO
          ================================================== */}

          <div className="hero">


            <div>

              <span className="eyebrow">
                LIVE · CODYSSEY EDGE NETWORK
              </span>


              <h1>

                City intelligence,{" "}

                <em>
                  in motion.
                </em>

              </h1>


              <p>

                Every bus becomes a mobile
                sensor. Detect locally, verify
                across the fleet, and turn road
                activity into actionable
                intelligence.

              </p>

            </div>


            <div className="hero-actions">


              <button
                className="secondary-btn"
              >

                <Radio
                  size={16}
                />


                {backendOnline
                  ? "Edge network online"
                  : "Connecting..."}

              </button>


              <button
                className="primary-btn"
                onClick={
                  fetchAlerts
                }
              >

                <Sparkles
                  size={16}
                />

                Refresh intelligence

              </button>

            </div>

          </div>


          {/* ==================================================
              STATS
          ================================================== */}

          <div className="stats-grid">


            <Stat
              icon={
                AlertTriangle
              }
              label="Active incidents"
              value={
                activeIncidents
              }
              detail={
                backendOnline
                  ? "Live from FastAPI"
                  : "Backend offline"
              }
              tone="pink"
            />


            <Stat
              icon={
                BusFront
              }
              label="Sensing fleet"
              value="42 / 48"
              detail="87.5% online"
              tone="cyan"
            />


            <Stat
              icon={
                Car
              }
              label="Traffic events"
              value={
                trafficEvents
              }
              detail={
                trafficEvents
                  ? "Detected by fleet"
                  : "No traffic alerts"
              }
              tone="amber"
            />


            <Stat
              icon={
                CheckCircle2
              }
              label="Avg confidence"
              value={
                `${averageConfidence}%`
              }
              detail={
                `${verifiedEvents} high-priority events`
              }
              tone="green"
            />

          </div>


          {/* ==================================================
              WORKSPACE
          ================================================== */}

          <div className="workspace">


            {/* MAP */}

            <section className="map-card">

              <MapPanel
                events={
                  alerts
                }
                selected={
                  selected
                }
                setSelected={
                  setSelected
                }
                showBuses={
                  showBuses
                }
                emergencyEvent={
                  emergencyEvent
                }
              />


              <div className="map-footer">


                <div className="map-metric">

                  <span>
                    Events today
                  </span>

                  <strong>
                    {activeIncidents}
                  </strong>

                </div>


                <div className="map-metric">

                  <span>
                    Road km sensed
                  </span>

                  <strong>
                    1,284 km
                  </strong>

                </div>


                <div className="map-metric">

                  <span>
                    Coverage
                  </span>

                  <strong>
                    78%
                  </strong>

                </div>


                <button
                  className={
                    "toggle " +
                    (
                      showBuses
                        ? "on"
                        : ""
                    )
                  }
                  onClick={() =>
                    setShowBuses(
                      !showBuses
                    )
                  }
                >

                  <span />

                  Show fleet

                </button>

              </div>

            </section>


            {/* =================================================
                RIGHT RAIL
            ================================================= */}

            <aside className="right-rail">


              {/* ===============================================
                  EMERGENCY
              =============================================== */}

              <div className="panel emergency-panel">


                <div className="panel-head">

                  <div>

                    <span className="eyebrow">
                      PRIORITY CORRIDOR
                    </span>

                    <h3>
                      Emergency response
                    </h3>

                  </div>


                  <Siren
                    size={18}
                  />

                </div>


                {/* ---------------------------------------------
                    AUTOMATIC EMERGENCY STATUS
                --------------------------------------------- */}

                <div
                  className={
                    "emergency-status " +
                    (
                      emergency
                        ? "active"
                        : ""
                    )
                  }
                >


                  <div className="siren-icon">

                    <Ambulance
                      size={21}
                    />

                  </div>


                  <div>

                    <strong>

                      {emergency
                        ? "AMBULANCE DETECTED"
                        : "NO ACTIVE EMERGENCY"}

                    </strong>


                    <small>

                      {emergency
                        ? `AI confidence ${
                            Math.round(
                              emergencyEvent.confidence *
                              100
                            )
                          }% · ${
                            emergencyEvent.bus
                          }`
                        : "AI monitoring all sensing buses"}

                    </small>

                  </div>

                </div>


                {/* ---------------------------------------------
                    AUTOMATIC CORRIDOR
                --------------------------------------------- */}

                {emergency && (

                  <>

                    <div
                      className="corridor"
                    >


                      <div
                        className="corridor-line"
                      >

                        <i />
                        <i />
                        <i />
                        <i />
                        <i />

                      </div>


                      <div>

                        <small>
                          AI-generated priority route
                        </small>

                        <strong>
                          Emergency vehicle → Destination
                        </strong>

                      </div>


                      <Badge
                        tone="verified"
                      >
                        4 SIGNALS
                      </Badge>

                    </div>


                    {/* NO BUTTON.
                        THIS IS SYSTEM OUTPUT. */}

                    <div
                      className="wide-btn"
                      style={{
                        cursor:
                          "default"
                      }}
                    >

                      🚦 SIGNAL PRIORITY REQUESTED

                    </div>


                    <div
                      style={{
                        marginTop:
                          "8px",
                        fontSize:
                          "10px",
                        color:
                          "var(--muted)"
                      }}
                    >

                      AI detection →
                      GPS location →
                      priority engine →
                      corridor generation

                    </div>

                  </>

                )}

              </div>


              {/* ===============================================
                  FLEET
              =============================================== */}

              <div
                className="panel fleet-panel"
              >

                <div
                  className="panel-head"
                >

                  <div>

                    <span className="eyebrow">
                      LIVE FLEET
                    </span>

                    <h3>
                      Mobile sensors
                    </h3>

                  </div>


                  <Badge
                    tone="live"
                  >
                    42 ONLINE
                  </Badge>

                </div>


                <div
                  className="fleet-list"
                >

                  {BUSES
                    .slice(0, 4)
                    .map(
                      bus => (

                        <button
                          key={
                            bus.id
                          }
                          className="fleet-row"
                          onClick={() => {

                            const event =
                              alerts.find(
                                item =>
                                  item.bus ===
                                  bus.id
                              );


                            if (
                              event
                            ) {

                              setSelected(
                                event
                              );

                            }

                          }}
                        >

                          <div
                            className="bus-icon"
                          >

                            <BusFront
                              size={16}
                            />

                          </div>


                          <div
                            className="fleet-main"
                          >

                            <strong>
                              {bus.id}
                            </strong>

                            <span>
                              Route{" "}
                              {bus.route}
                              {" · "}
                              {bus.speed}
                              {" "}
                              km/h
                            </span>

                          </div>


                          <div
                            className="fleet-state"
                          >

                            <i />

                            {bus.events}
                            {" "}
                            events

                          </div>

                        </button>

                      )
                    )}

                </div>

              </div>


              {/* ===============================================
                  AI INSIGHT
              =============================================== */}

              <div
                className="panel insight-panel"
              >

                <div
                  className="insight-icon"
                >

                  <Zap
                    size={17}
                  />

                </div>


                <div>

                  <span
                    className="eyebrow"
                  >
                    AI INSIGHT
                  </span>


                  <p>

                    {emergency

                      ? (
                        <>
                          <strong>
                            Emergency vehicle
                            detected.
                          </strong>{" "}
                          AI has generated a
                          priority corridor
                          using the detected
                          vehicle location.
                        </>
                      )

                      : trafficEvents > 0

                        ? `${trafficEvents} traffic event(s) are currently being reported by the sensing fleet.`

                        : "The sensing fleet is monitoring the road network for traffic anomalies."

                    }

                  </p>

                </div>

              </div>

            </aside>

          </div>


          {/* ==================================================
              EVENTS
          ================================================== */}

          <section
            className="panel events-panel"
          >


            <div
              className="panel-head event-head"
            >

              <div>

                <span className="eyebrow">
                  EVENT STREAM
                </span>

                <h3>
                  Latest urban intelligence
                </h3>

              </div>


              <div
                className="filter-row"
              >

                {[
                  "All",
                  "Road",
                  "Traffic",
                  "Infrastructure",
                  "Unsafe"
                ].map(
                  category => (

                    <button
                      key={
                        category
                      }
                      className={
                        filter ===
                        category
                          ? "selected"
                          : ""
                      }
                      onClick={() =>
                        setFilter(
                          category
                        )
                      }
                    >

                      {category}

                    </button>

                  )
                )}

              </div>

            </div>


            <div
              className="events-table"
            >


              <div
                className="table-row table-header"
              >

                <span>
                  EVENT
                </span>

                <span>
                  LOCATION
                </span>

                <span>
                  SOURCE
                </span>

                <span>
                  CONFIDENCE
                </span>

                <span>
                  STATUS
                </span>

                <span />

              </div>


              {loading && (

                <div
                  className="table-row"
                  style={{
                    display:
                      "block",
                    color:
                      "var(--muted)"
                  }}
                >

                  Connecting to
                  CODYSSEY backend...

                </div>

              )}


              {!loading &&
                filtered.length ===
                  0 && (

                <div
                  className="table-row"
                  style={{
                    display:
                      "block",
                    color:
                      "var(--muted)"
                  }}
                >

                  {backendOnline
                    ? "No alerts have been generated yet."
                    : "FastAPI backend is offline."}

                </div>

              )}


              {filtered.map(
                event => {

                  const Icon =
                    ICONS[
                      event.category
                    ] ||
                    AlertTriangle;


                  return (

                    <button
                      className={
                        "table-row event-row " +
                        (
                          selected?.id ===
                          event.id
                            ? "selected-row"
                            : ""
                        )
                      }
                      key={
                        event.id
                      }
                      onClick={() =>
                        setSelected(
                          event
                        )
                      }
                    >


                      {/* EVENT */}

                      <span
                        className="event-name"
                      >

                        <div
                          className={
                            "event-icon " +
                            event.category
                          }
                        >

                          <Icon
                            size={16}
                          />

                        </div>


                        <div>

                          <strong>

                            {event.type}

                          </strong>


                          <small>

                            {event.id}
                            {" · "}
                            {event.time}

                          </small>

                        </div>

                      </span>


                      {/* LOCATION */}

                      <span
                        className="location-cell"
                      >

                        <MapPin
                          size={14}
                        />

                        {event.location}

                      </span>


                      {/* SOURCE */}

                      <span
                        className="source-cell"
                      >

                        {event.category ===
                        "emergency"

                          ? (
                            <Ambulance
                              size={14}
                            />
                          )

                          : (
                            <BusFront
                              size={14}
                            />
                          )
                        }


                        {event.bus}


                        <small>

                          {event.category ===
                          "emergency"
                            ? "AI emergency detection"
                            : "Live bus source"}

                        </small>

                      </span>


                      {/* CONFIDENCE */}

                      <span
                        className="confidence"
                      >

                        <strong>

                          {Math.round(
                            event.confidence *
                            100
                          )}
                          %

                        </strong>


                        <div
                          className="confidence-bar"
                        >

                          <i
                            style={{
                              width:
                                `${
                                  event.confidence *
                                  100
                                }%`
                            }}
                          />

                        </div>

                      </span>


                      {/* STATUS */}

                      <span>

                        <Badge
                          tone={
                            event.category ===
                            "emergency"
                              ? "verified"
                              : event.priority >=
                                80
                                ? "verified"
                                : "review"
                          }
                        >

                          {event.category ===
                          "emergency"
                            ? "CRITICAL"
                            : event.status}

                        </Badge>

                      </span>


                      <span>

                        <ChevronRight
                          size={16}
                        />

                      </span>

                    </button>

                  );
                }
              )}

            </div>

          </section>


          {/* ==================================================
              FOOTER
          ================================================== */}

          <footer>

            <span>

              <span
                className="pulse small"
              />

              CODYSSEY edge network{" "}

              {backendOnline
                ? "operational"
                : "waiting for backend"}

            </span>


            <span>

              AI inference stays on-device
              · Event metadata only
              · v1.0 prototype

            </span>

          </footer>

        </section>

      </main>

    </div>
  );
}


// ============================================================
// RENDER
// ============================================================

createRoot(
  document.getElementById(
    "root"
  )
).render(

  <React.StrictMode>

    <App />

  </React.StrictMode>

);