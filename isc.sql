CREATE DATABASE ISC;
USE ISC;

DROP TABLE IF EXISTS student;
CREATE TABLE student(
  roll_no bigint NOT NULL,
  Name varchar(255) DEFAULT NULL,
  Email varchar(255) DEFAULT NULL,
  password varchar(50) DEFAULT NULL,
  Phone_No bigint DEFAULT NULL,
  Department varchar(50) DEFAULT NULL,
  Year int DEFAULT NULL,
  PRIMARY KEY (roll_no)
);

DROP TABLE IF EXISTS sport;
CREATE TABLE sport(
  id int NOT NULL,
  Type varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
);

DROP TABLE IF EXISTS booking;
CREATE TABLE booking(
  id bigint NOT NULL AUTO_INCREMENT,
  room_id int DEFAULT NULL,
  booked_date date NOT NULL,
  booked_time time NOT NULL,
  student_id bigint DEFAULT NULL,
  time_of_booking timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status ENUM('Pending', 'Accepted', 'Denied') DEFAULT 'Pending',
  is_blacklist BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (id),
  UNIQUE KEY uc1 (room_id,booked_date,booked_time),
  KEY fk1 (student_id),
  CONSTRAINT fk1 FOREIGN KEY (student_id) REFERENCES student (roll_no) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk2 FOREIGN KEY (room_id) REFERENCES sport (id) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TABLE IF EXISTS supervisor;
CREATE TABLE supervisor(
  id bigint NOT NULL,
  name varchar(255) DEFAULT NULL,
  email varchar(255) DEFAULT NULL,
  password varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

DROP TABLE IF EXISTS blacklist;
CREATE TABLE blacklist (
    roll_no bigint NOT NULL,
    reason varchar(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE blacklist
ADD CONSTRAINT fk_blacklist_student
FOREIGN KEY (roll_no)
REFERENCES student(roll_no);

CREATE PROCEDURE search_room(IN p_type VARCHAR(255), IN p_booked_date DATE, IN p_booked_time TIME)
BEGIN
    SELECT s.id, s.Type 
    FROM sport s
    LEFT JOIN booking b ON s.id = b.room_id AND b.booked_date = p_booked_date AND b.booked_time = p_booked_time AND b.status != 'Denied'
    WHERE s.type = p_type AND b.room_id IS NULL;
    IF ROW_COUNT() = 0 THEN
        SELECT 'No rooms available for the specified date and time' AS message;
    END IF;
END;

CREATE PROCEDURE view_booking(in p_id bigint)
BEGIN
SELECT b.id, s.Type, b.booked_date, b.booked_time, b.status
        FROM booking b
        JOIN sport s ON b.room_id = s.id
        WHERE b.student_id = '%s'
        ORDER BY b.booked_date DESC, b.booked_time DESC;
END;

CREATE PROCEDURE get_pending_bookings()
BEGIN
    SELECT id, room_id, booked_date, booked_time, student_id, status 
    FROM booking 
    WHERE status = 'Pending';
END;

CREATE PROCEDURE update_booking_request(p_booking_id bigint, p_status ENUM('Accepted', 'Denied'))
BEGIN
    UPDATE booking
    SET status = p_status
    WHERE id = p_booking_id;
END;
  
CREATE TRIGGER before_booking
BEFORE INSERT ON booking
FOR EACH ROW
BEGIN
    DECLARE is_blacklisted INT;

    SELECT COUNT(*) INTO is_blacklisted
    FROM blacklist
    WHERE roll_no = NEW.student_id;

    IF is_blacklisted > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Student is blacklisted and cannot make booking';
    END IF;
END//
