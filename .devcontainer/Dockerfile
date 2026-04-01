# ============================================================
# HDL Verification Ecosystem - Custom Docker Image
# Tools: Icarus Verilog, GTKWave, Yosys, Netlistsvg, OpenSTA
# ============================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# ── Base system ──────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    # Core utilities
    curl wget git build-essential python3 python3-pip \
    # Simulation
    iverilog \
    # GTKWave + virtual display
    gtkwave xvfb xauth \
    # Yosys (synthesis)
    yosys \
    # Graphviz (dot → svg for schematics)
    graphviz \
    # OpenSTA dependencies
    tcl-dev swig libreadline-dev bison flex \
    # Misc
    jq bc \
    && rm -rf /var/lib/apt/lists/*

# ── Python tools ─────────────────────────────────────────────
RUN pip3 install --no-cache-dir \
    netlistsvg \
    yowasp-yosys \
    pandas \
    matplotlib

# ── Netlistsvg (JS-based schematic renderer) ─────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g netlistsvg \
    && rm -rf /var/lib/apt/lists/*

# ── OpenSTA (Static Timing Analysis) ─────────────────────────
RUN apt-get update && apt-get install -y cmake libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth=1 https://github.com/The-OpenROAD-Project/OpenSTA.git /opt/opensta \
    && cd /opt/opensta \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local \
    && make -j$(nproc) \
    && make install \
    && rm -rf /opt/opensta

# ── Liberty timing lib (generic, for educational use) ─────────
RUN mkdir -p /opt/timing_libs
COPY timing_libs/generic_timing.lib /opt/timing_libs/generic_timing.lib

# ── Set working directory ─────────────────────────────────────
WORKDIR /workspace

CMD ["/bin/bash"]
