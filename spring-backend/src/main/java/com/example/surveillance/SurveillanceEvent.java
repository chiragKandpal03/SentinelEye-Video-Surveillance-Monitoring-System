package com.example.surveillance;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "surveillance_events")
public class SurveillanceEvent {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 40)
    private String eventType;

    @Column(nullable = false, length = 500)
    private String description;

    private Double confidence;

    @Column(length = 1000)
    private String snapshotPath;

    @Column(nullable = false, length = 100)
    private String source = "python-ai";

    @Column(nullable = false)
    private Instant occurredAt = Instant.now();

    public SurveillanceEvent() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getEventType() { return eventType; }
    public void setEventType(String eventType) { this.eventType = eventType; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }
    public String getSnapshotPath() { return snapshotPath; }
    public void setSnapshotPath(String snapshotPath) { this.snapshotPath = snapshotPath; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Instant getOccurredAt() { return occurredAt; }
    public void setOccurredAt(Instant occurredAt) { this.occurredAt = occurredAt; }
}
