/**
 * Frontend Face Recognition Service using face-api.js
 * This runs entirely in the browser using WebGL acceleration.
 */
import * as faceapi from 'face-api.js';
import { API_BASE } from '../config';

const MODEL_URL = '/models'; // Public folder for face-api.js models

export interface FaceMatch {
  name: string;
  distance: number;
  box: { x: number; y: number; width: number; height: number };
}

class FaceRecognitionService {
  private labeledDescriptors: faceapi.LabeledFaceDescriptors[] = [];
  private modelsLoaded = false;
  private initialized = false;

  /**
   * Load face-api.js models from public folder
   */
  async loadModels(): Promise<void> {
    if (this.modelsLoaded) return;
    
    console.log('[FaceService] Loading face-api.js models...');
    await Promise.all([
      faceapi.nets.ssdMobilenetv1.loadFromUri(MODEL_URL),
      faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
      faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
    ]);
    this.modelsLoaded = true;
    console.log('[FaceService] Models loaded successfully!');
  }

  /**
   * Fetch team images from backend and create labeled descriptors
   */
  async loadFaceDatabase(): Promise<void> {
    if (this.initialized) return;
    
    await this.loadModels();
    
    console.log('[FaceService] Fetching face manifest from backend...');
    
    try {
      const response = await fetch(`${API_BASE}/api/faces/manifest`);
      const manifest: { people: { name: string; images: string[] }[] } = await response.json();
      
      console.log(`[FaceService] Found ${manifest.people.length} people in database`);
      
      const labeledDescriptorsPromises = manifest.people.map(async (person) => {
        const descriptors: Float32Array[] = [];
        
        for (const imageUrl of person.images.slice(0, 5)) { // Limit to 5 images per person
          try {
            const img = await faceapi.fetchImage(`${API_BASE}${imageUrl}`);
            const detection = await faceapi
              .detectSingleFace(img)
              .withFaceLandmarks()
              .withFaceDescriptor();
            
            if (detection) {
              descriptors.push(detection.descriptor);
            }
          } catch (e) {
            console.warn(`[FaceService] Failed to load image: ${imageUrl}`);
          }
        }
        
        if (descriptors.length > 0) {
          console.log(`[FaceService] Loaded ${descriptors.length} descriptors for "${person.name}"`);
          return new faceapi.LabeledFaceDescriptors(person.name, descriptors);
        }
        return null;
      });
      
      const results = await Promise.all(labeledDescriptorsPromises);
      this.labeledDescriptors = results.filter((d): d is faceapi.LabeledFaceDescriptors => d !== null);
      this.initialized = true;
      
      console.log(`[FaceService] Database initialized with ${this.labeledDescriptors.length} people`);
    } catch (error) {
      console.error('[FaceService] Failed to load face database:', error);
      throw error;
    }
  }

  /**
   * Detect and recognize faces in a video element
   */
  async detectFaces(video: HTMLVideoElement): Promise<FaceMatch[]> {
    if (!this.initialized || this.labeledDescriptors.length === 0) {
      return [];
    }
    
    const detections = await faceapi
      .detectAllFaces(video)
      .withFaceLandmarks()
      .withFaceDescriptors();
    
    if (detections.length === 0) return [];
    
    const faceMatcher = new faceapi.FaceMatcher(this.labeledDescriptors, 0.6);
    
    return detections.map((detection) => {
      const match = faceMatcher.findBestMatch(detection.descriptor);
      const box = detection.detection.box;
      
      return {
        name: match.label === 'unknown' ? 'Unknown' : match.label,
        distance: match.distance,
        box: {
          x: box.x,
          y: box.y,
          width: box.width,
          height: box.height,
        },
      };
    });
  }

  /**
   * Mark attendance on the backend
   */
  async markAttendance(name: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE}/api/simple-attendance/mark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, timestamp: new Date().toISOString() }),
      });
      const result = await response.json();
      console.log('[FaceService] Attendance mark result:', result);
      return response.ok;
    } catch (e) {
      console.error('[FaceService] Failed to mark attendance:', e);
      return false;
    }
  }

  /**
   * Get list of enrolled people
   */
  getEnrolledPeople(): string[] {
    return this.labeledDescriptors.map((d) => d.label);
  }

  isReady(): boolean {
    return this.initialized;
  }
}

export const faceRecognitionService = new FaceRecognitionService();
export default faceRecognitionService;
