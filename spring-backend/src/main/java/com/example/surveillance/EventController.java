package com.example.surveillance;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class EventController {
    private final EventRepository repository;

    public EventController(EventRepository repository) {
        this.repository = repository;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "AI Smart Surveillance API");
    }

    @GetMapping("/events")
    public List<SurveillanceEvent> events() {
        return repository.findTop200ByOrderByOccurredAtDesc();
    }

    @PostMapping("/events")
    @ResponseStatus(HttpStatus.CREATED)
    public SurveillanceEvent create(@RequestBody SurveillanceEvent event) {
        if (event.getEventType() == null || event.getEventType().isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "eventType is required");
        }
        if (event.getDescription() == null || event.getDescription().isBlank()) {
            event.setDescription("No description provided");
        }
        if (event.getSource() == null || event.getSource().isBlank()) {
            event.setSource("python-ai");
        }
        if (event.getOccurredAt() == null) {
            event.setOccurredAt(Instant.now());
        }
        return repository.save(event);
    }

    @DeleteMapping("/events/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        if (!repository.existsById(id)) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Event not found");
        }
        repository.deleteById(id);
    }
}
