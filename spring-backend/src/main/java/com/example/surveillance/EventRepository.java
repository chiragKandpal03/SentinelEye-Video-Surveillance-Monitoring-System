package com.example.surveillance;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface EventRepository extends JpaRepository<SurveillanceEvent, Long> {
    List<SurveillanceEvent> findTop200ByOrderByOccurredAtDesc();
}
