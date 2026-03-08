# Build GDAL/GEOS/PROJ from source for GeoDjango support
# Multi-stage build: compile in builder, copy only runtime artifacts to final image
# This base image is cached in ECR and reused across deployments

# Stage 1: Builder - compile all geospatial libraries
FROM public.ecr.aws/lambda/python:3.14 AS builder

ENV GDAL_VERSION=3.12.2 \
    GEOS_VERSION=3.14.1 \
    PROJ_VERSION=9.7.1

# Install build dependencies (Amazon Linux 2023 uses dnf)
RUN dnf install -y \
    gcc gcc-c++ make cmake \
    sqlite sqlite-devel \
    libcurl-devel \
    libtiff libtiff-devel \
    tar gzip bzip2 xz \
    && dnf clean all

# Build PROJ (required by GDAL)
WORKDIR /tmp
RUN curl -L https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz | tar xz && \
    cd proj-${PROJ_VERSION} && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/opt \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=OFF \
        .. && \
    make -j2 && \
    make install && \
    cd ../.. && rm -rf proj-${PROJ_VERSION}

# Build GEOS (required by GDAL for geometry operations)
RUN curl -L https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 | tar xj && \
    cd geos-${GEOS_VERSION} && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/opt \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=OFF \
        .. && \
    make -j2 && \
    make install && \
    cd ../.. && rm -rf geos-${GEOS_VERSION}

# Build GDAL
RUN curl -L https://github.com/OSGeo/gdal/releases/download/v${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz | tar xz && \
    cd gdal-${GDAL_VERSION} && \
    mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/opt \
        -DCMAKE_BUILD_TYPE=Release \
        -DBUILD_TESTING=OFF \
        -DGDAL_USE_GEOS=ON \
        -DGEOS_INCLUDE_DIR=/opt/include \
        -DGEOS_LIBRARY=/opt/lib64/libgeos_c.so \
        -DPROJ_ROOT=/opt \
        .. && \
    make -j2 && \
    make install && \
    cd ../.. && rm -rf gdal-${GDAL_VERSION}

# Set paths for Python GDAL bindings install
ENV LD_LIBRARY_PATH=/opt/lib64:$LD_LIBRARY_PATH \
    PATH=/opt/bin:$PATH

RUN mkdir -p /opt/lib

# Install Python GDAL bindings matching the compiled version
RUN GDAL_CONFIG=/opt/bin/gdal-config \
    CPPFLAGS="-I/opt/include" \
    LDFLAGS="-L/opt/lib64" \
    pip install --no-cache-dir GDAL==${GDAL_VERSION}

# Stage 2: Runtime - clean image with only compiled artifacts
FROM public.ecr.aws/lambda/python:3.14 AS geolambda

ENV GDAL_VERSION=3.12.2 \
    GEOS_VERSION=3.14.1 \
    PROJ_VERSION=9.7.1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN dnf install -y libtiff && dnf clean all

# Copy compiled libraries, binaries, and data from builder
COPY --from=builder /opt/lib64/ /opt/lib64/
COPY --from=builder /opt/lib/ /opt/lib/
COPY --from=builder /opt/bin/ /opt/bin/
COPY --from=builder /opt/share/ /opt/share/

# Copy Python site-packages (including GDAL bindings) from builder
COPY --from=builder /var/lang/lib/python3.14/site-packages/ /var/lang/lib/python3.14/site-packages/

ENV LD_LIBRARY_PATH=/opt/lib:/opt/lib64:$LD_LIBRARY_PATH \
    GDAL_DATA=/opt/share/gdal \
    PROJ_DATA=/opt/share/proj \
    PROJ_LIB=/opt/share/proj \
    PATH=/opt/bin:$PATH

# Verify installation
RUN python -c "from osgeo import gdal, ogr, osr; print(f'GDAL {gdal.__version__} installed successfully')"

LABEL description="Base Lambda image with GDAL/GEOS/PROJ for GeoDjango" \
      gdal.version="${GDAL_VERSION}" \
      geos.version="${GEOS_VERSION}" \
      proj.version="${PROJ_VERSION}"
