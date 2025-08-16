# SAGE - Technical Specification

## 🎯 **System Overview**

SAGE is an AI-powered video comparison system that analyzes video content at the segment level using machine learning embeddings. The system processes video files through an AI service, generates semantic representations of video segments, and provides tools to compare videos by identifying differences in content, timing, and visual elements.

## 🏗️ **Core Architecture Concepts**

### **System Components**

#### **Frontend Application**
- **Purpose**: User interface for video upload, processing management, and comparison visualization
- **Primary Functions**: 
  - Video file selection and upload interface
  - Real-time progress tracking during AI processing
  - Side-by-side video comparison with synchronized playback
  - Interactive timeline with difference markers
  - Configuration management for AI parameters

#### **Backend API Server**
- **Purpose**: Central processing hub that coordinates between frontend, AI services, and data storage
- **Primary Functions**:
  - File upload handling and temporary storage
  - AI service integration and task management
  - Video comparison computation using vector mathematics
  - Video streaming for playback
  - API key validation and security management

#### **AI Processing Service**
- **Purpose**: External service that converts video content into mathematical representations
- **Primary Functions**:
  - Video segmentation into time-based chunks
  - Feature extraction from each segment
  - Generation of high-dimensional vector embeddings
  - Semantic understanding of video content

#### **Data Storage Layer**
- **Purpose**: Persistent storage for system metadata and temporary storage for video content
- **Primary Functions**:
  - API key storage with cryptographic hashing
  - Video file temporary storage during processing
  - Embedding vector storage for comparison operations
  - Session and configuration persistence

### **Data Flow Architecture**

#### **Phase 1: Initialization**
1. User provides AI service API credentials
2. System validates credentials against external AI service
3. Credentials are cryptographically hashed and stored
4. User session is established with credential caching

#### **Phase 2: Video Processing**
1. User selects video files through web interface
2. Files are uploaded to backend server via HTTP multipart requests
3. Backend creates processing tasks with AI service
4. AI service processes videos asynchronously:
   - Extracts video segments at regular time intervals
   - Generates embedding vectors for each segment
   - Returns structured data with timestamps and vectors
5. Backend stores processed data in memory for comparison operations

#### **Phase 3: Comparison Analysis**
1. User initiates comparison between two processed videos
2. System retrieves embedding vectors for both videos
3. For each time segment, system calculates similarity metrics:
   - Cosine distance between corresponding segment vectors
   - Euclidean distance as alternative metric
   - Threshold-based filtering of differences
4. Results are structured with timestamps, distance values, and metadata

#### **Phase 4: Visualization**
1. Comparison results are transmitted to frontend
2. Frontend renders synchronized video players
3. Timeline overlay displays difference markers
4. User can adjust similarity thresholds for real-time filtering
5. Video playback controls are synchronized between both players

## 🔧 **Core Technical Concepts**

### **Video Processing Pipeline**

#### **Segment-Based Analysis**
- **Concept**: Videos are divided into fixed-duration segments (typically 2-second intervals)
- **Purpose**: Enables granular comparison at specific time points
- **Implementation**: Each segment becomes a discrete unit for AI analysis and comparison

#### **Embedding Vector Generation**
- **Concept**: AI service converts visual content into high-dimensional numerical vectors
- **Purpose**: Enables mathematical comparison of video content
- **Characteristics**: 
  - Vectors represent semantic meaning, not just pixel data
  - Similar content produces similar vectors regardless of exact pixel values
  - Vectors are normalized for consistent comparison

#### **Asynchronous Processing**
- **Concept**: AI processing happens in background while user interface remains responsive
- **Purpose**: Handles long-running AI tasks without blocking user interaction
- **Implementation**: Task queuing, status polling, and progress reporting

### **Comparison Algorithm**

#### **Vector Similarity Metrics**
- **Cosine Distance**: Measures angle between vectors, range 0-1 (0 = identical, 1 = completely different)
- **Euclidean Distance**: Measures straight-line distance between vector points
- **Threshold Filtering**: User-configurable sensitivity for difference detection

#### **Temporal Alignment**
- **Concept**: Segments from different videos are aligned by timestamp
- **Purpose**: Ensures comparison of corresponding time periods
- **Handling**: Manages videos of different lengths and segment counts

#### **Difference Detection**
- **Process**: Compare corresponding segments, calculate distance, apply threshold
- **Output**: List of segments where distance exceeds threshold
- **Metadata**: Timestamps, distance values, and segment information

### **User Interface Concepts**

#### **Real-Time Progress Tracking**
- **Concept**: Continuous updates during long-running operations
- **Implementation**: Polling mechanism with status indicators
- **User Experience**: Clear feedback on processing stages and completion

#### **Synchronized Video Playback**
- **Concept**: Two video players with coordinated controls
- **Features**: 
  - Play/pause synchronization
  - Timeline scrubbing coordination
  - Current time display
  - Difference marker overlay

#### **Interactive Timeline**
- **Concept**: Visual representation of video timeline with difference indicators
- **Features**:
  - Color-coded difference markers
  - Clickable segments for navigation
  - Threshold adjustment controls
  - Statistical information display

#### **Responsive Design**
- **Concept**: Interface adapts to different screen sizes and devices
- **Implementation**: CSS-based layout with mobile-first approach
- **Features**: Touch-friendly controls, adaptive video player sizing

### **Security and Authentication**

#### **API Key Management**
- **Concept**: Secure storage and validation of external service credentials
- **Implementation**: 
  - Cryptographic hashing before storage
  - Validation against external service
  - Session-based caching for performance

#### **Input Validation**
- **Concept**: Verification of all user inputs and file uploads
- **Checks**: File type validation, size limits, format verification
- **Security**: Prevention of malicious file uploads and injection attacks

#### **CORS and Access Control**
- **Concept**: Control of cross-origin requests and resource access
- **Implementation**: Configurable origin whitelist and method restrictions
- **Security**: Prevention of unauthorized cross-site requests

## 📊 **Data Structures and Models**

### **Video Processing Data**
```typescript
interface VideoSegment {
  start_time: number;      // Start timestamp in seconds
  end_time: number;        // End timestamp in seconds
  embedding_vector: number[];  // High-dimensional feature vector
  metadata: object;        // Additional segment information
}

interface ProcessedVideo {
  video_id: string;        // Unique identifier
  filename: string;        // Original filename
  duration: number;        // Total duration in seconds
  segments: VideoSegment[]; // Array of processed segments
  processing_status: 'pending' | 'processing' | 'completed' | 'error';
  created_at: timestamp;   // Processing timestamp
}
```

### **Comparison Results**
```typescript
interface DifferenceSegment {
  start_sec: number;       // Start time of difference
  end_sec: number;         // End time of difference
  distance: number;        // Similarity distance value
  severity: 'low' | 'medium' | 'high'; // Difference magnitude
}

interface ComparisonResult {
  video1_id: string;       // First video identifier
  video2_id: string;       // Second video identifier
  differences: DifferenceSegment[]; // Array of detected differences
  total_segments: number;  // Total segments compared
  differing_segments: number; // Number of segments with differences
  threshold_used: number;  // Similarity threshold applied
  distance_metric: 'cosine' | 'euclidean'; // Metric used
}
```

### **System Configuration**
```typescript
interface SystemConfig {
  ai_service_config: {
    api_key: string;       // External AI service credentials
    model_name: string;    // AI model identifier
    segment_duration: number; // Segment length in seconds
  };
  comparison_config: {
    default_threshold: number; // Default similarity threshold
    distance_metric: string;   // Default distance calculation method
    max_file_size: number;     // Maximum upload file size
  };
  ui_config: {
    theme: 'light' | 'dark';   // Interface theme
    language: string;          // Interface language
    auto_play: boolean;        // Auto-play videos on load
  };
}
```

## 🔄 **Process Flows**

### **Video Upload and Processing Flow**

1. **File Selection**
   - User selects video files through web interface
   - System validates file type and size
   - Files are prepared for upload

2. **Upload Process**
   - Files are transmitted to backend via HTTP
   - Backend stores files temporarily
   - Upload progress is reported to frontend

3. **AI Processing Initiation**
   - Backend creates processing tasks with AI service
   - Task IDs are returned and stored
   - Processing status is set to 'pending'

4. **Background Processing**
   - AI service processes videos asynchronously
   - Backend polls for completion status
   - Progress updates are sent to frontend

5. **Data Storage**
   - Processed embeddings are stored in memory
   - Video metadata is updated
   - Processing status is set to 'completed'

### **Comparison Analysis Flow**

1. **Comparison Request**
   - User selects two processed videos
   - System validates both videos are ready
   - Comparison parameters are configured

2. **Vector Retrieval**
   - Embedding vectors are loaded from storage
   - Temporal alignment is performed
   - Segment pairs are prepared for comparison

3. **Similarity Calculation**
   - For each segment pair, distance is calculated
   - Results are filtered by threshold
   - Difference segments are identified

4. **Result Processing**
   - Differences are sorted by timestamp
   - Statistical information is calculated
   - Results are formatted for frontend

5. **Visualization**
   - Results are transmitted to frontend
   - Timeline markers are generated
   - Video players are synchronized

### **Real-Time Interaction Flow**

1. **Threshold Adjustment**
   - User modifies similarity threshold
   - New comparison is calculated
   - Results are updated in real-time
   - Timeline markers are refreshed

2. **Video Navigation**
   - User scrubs timeline or clicks markers
   - Both video players seek to same timestamp
   - Current time display is updated
   - Difference information is highlighted

3. **Playback Control**
   - User controls one video player
   - Other player synchronizes automatically
   - Timeline position updates continuously
   - Difference markers remain visible

## 🎨 **User Experience Design**

### **Information Architecture**

#### **Primary User Journey**
1. **Setup**: Configure AI service credentials
2. **Upload**: Select and upload video files
3. **Processing**: Monitor AI processing progress
4. **Comparison**: Initiate and configure comparison
5. **Analysis**: Review results and adjust parameters
6. **Export**: Save or share comparison results

#### **Interface Hierarchy**
- **Global Navigation**: System-wide controls and settings
- **Page-Level**: Primary task interfaces (upload, analysis)
- **Component-Level**: Specific functionality (video player, timeline)
- **Element-Level**: Individual controls and indicators

### **Visual Design Principles**

#### **Clarity and Simplicity**
- **Minimal Interface**: Focus on essential functionality
- **Clear Hierarchy**: Visual organization of information
- **Consistent Patterns**: Reusable design elements
- **Progressive Disclosure**: Show information as needed

#### **Feedback and Status**
- **Loading States**: Clear indication of processing
- **Progress Indicators**: Real-time status updates
- **Error Handling**: Helpful error messages and recovery
- **Success Confirmation**: Clear completion indicators

#### **Accessibility**
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Semantic HTML and ARIA labels
- **Color Contrast**: WCAG compliant color ratios
- **Responsive Design**: Works across device sizes

### **Interaction Patterns**

#### **Drag and Drop**
- **Visual Feedback**: Clear drop zones and states
- **File Validation**: Immediate feedback on file types
- **Progress Indication**: Upload progress visualization
- **Error Recovery**: Clear error messages and retry options

#### **Real-Time Updates**
- **Polling Mechanism**: Regular status checks
- **WebSocket Alternative**: Real-time communication
- **Optimistic Updates**: Immediate UI feedback
- **Error Handling**: Graceful degradation

#### **Modal and Overlay**
- **Configuration Panels**: Settings and parameter adjustment
- **Error Dialogs**: Clear error presentation
- **Confirmation Dialogs**: User action confirmation
- **Help and Documentation**: Contextual assistance

## 🔧 **Technical Implementation Considerations**

### **Performance Optimization**

#### **Frontend Performance**
- **Code Splitting**: Load components on demand
- **Lazy Loading**: Defer non-critical resources
- **Caching Strategy**: Browser and application caching
- **Bundle Optimization**: Minimize JavaScript bundle size

#### **Backend Performance**
- **Connection Pooling**: Efficient database connections
- **Memory Management**: Proper cleanup of temporary data
- **Async Processing**: Non-blocking operations
- **Caching Layers**: Application and database caching

#### **Network Optimization**
- **Compression**: Gzip compression for responses
- **CDN Integration**: Content delivery network
- **API Batching**: Combine multiple requests
- **Pagination**: Large dataset handling

### **Scalability Considerations**

#### **Horizontal Scaling**
- **Stateless Design**: No server-side session storage
- **Load Balancing**: Distribute requests across servers
- **Database Scaling**: Read replicas and sharding
- **Microservices**: Decompose into smaller services

#### **Vertical Scaling**
- **Resource Monitoring**: CPU, memory, and disk usage
- **Performance Profiling**: Identify bottlenecks
- **Optimization**: Algorithm and data structure improvements
- **Caching**: Reduce computational overhead

### **Security Implementation**

#### **Data Protection**
- **Encryption**: Data in transit and at rest
- **Access Control**: Role-based permissions
- **Audit Logging**: Track system access and changes
- **Input Sanitization**: Prevent injection attacks

#### **API Security**
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Authentication**: Secure credential management
- **Authorization**: Resource access control
- **Validation**: Comprehensive input validation

### **Monitoring and Observability**

#### **Application Monitoring**
- **Health Checks**: System status monitoring
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Exception monitoring and alerting
- **User Analytics**: Usage patterns and behavior

#### **Infrastructure Monitoring**
- **Server Metrics**: CPU, memory, disk, and network
- **Database Performance**: Query times and connection pools
- **External Service Monitoring**: AI service availability
- **Log Aggregation**: Centralized logging and analysis

## 🚀 **Deployment Architecture**

### **Development Environment**
- **Local Development**: Docker containers for consistency
- **Hot Reloading**: Real-time code changes
- **Debug Tools**: Integrated debugging and profiling
- **Testing Framework**: Unit and integration tests

### **Staging Environment**
- **Production Parity**: Identical to production setup
- **Data Seeding**: Test data for validation
- **Performance Testing**: Load and stress testing
- **Security Testing**: Vulnerability assessment

### **Production Environment**
- **High Availability**: Redundant systems and failover
- **Auto Scaling**: Dynamic resource allocation
- **Backup Strategy**: Data backup and recovery
- **Disaster Recovery**: Business continuity planning

### **CI/CD Pipeline**
- **Automated Testing**: Code quality and functionality
- **Security Scanning**: Vulnerability detection
- **Deployment Automation**: Zero-downtime deployments
- **Rollback Strategy**: Quick recovery from issues

## 📋 **Development Guidelines**

### **Code Organization**
- **Modular Architecture**: Separation of concerns
- **Consistent Patterns**: Standardized implementation approaches
- **Documentation**: Code comments and API documentation
- **Version Control**: Git workflow and branching strategy

### **Testing Strategy**
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete user journey testing
- **Performance Tests**: Load and stress testing

### **Quality Assurance**
- **Code Review**: Peer review process
- **Static Analysis**: Automated code quality checks
- **Security Review**: Security-focused code analysis
- **Performance Review**: Performance impact assessment

---

This technical specification provides the conceptual foundation for building a video comparison system from scratch, focusing on the core concepts, architecture, and functionality rather than specific implementation details.
