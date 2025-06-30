DROP DATABASE LEMONA_GMP;

CREATE DATABASE LEMONA_GMP;

USE LEMONA_GMP;

CREATE TABLE USER (
    USER_ID VARCHAR(50) PRIMARY KEY,
    PW VARCHAR(255),
    NAME VARCHAR(100),
    DIVISION VARCHAR(100),
    STATUS BOOLEAN DEFAULT TRUE,
    ROLE_ID INT,
    PW_UPDATE_DT DATE,
    CREATE_DT DATE,
    UPDATE_DT DATE
);

CREATE TABLE ROLE (
    ROLE_ID INT PRIMARY KEY AUTO_INCREMENT,
    ROLE_NAME VARCHAR(50)
);

CREATE TABLE ACCESS (
    ACCESS_ID INT PRIMARY KEY AUTO_INCREMENT,
    ROLE_ID INT NOT NULL,
    PAGE_ID INT NOT NULL
);

CREATE TABLE PAGE (
    PAGE_ID INT PRIMARY KEY AUTO_INCREMENT,
    PAGE_LINK VARCHAR(100),
    MENU_NAME VARCHAR(100),
    PAGE_NAME VARCHAR(100)
);

ALTER TABLE USER 
ADD CONSTRAINT FK_USER_ROLE 
FOREIGN KEY (ROLE_ID) REFERENCES ROLE(ROLE_ID);

ALTER TABLE ACCESS 
ADD CONSTRAINT FK_ACCESS_ROLE 
FOREIGN KEY (ROLE_ID) REFERENCES ROLE(ROLE_ID);

ALTER TABLE ACCESS 
ADD CONSTRAINT FK_ACCESS_PAGE 
FOREIGN KEY (PAGE_ID) REFERENCES PAGE(PAGE_ID);

INSERT INTO ROLE (ROLE_NAME) VALUES 
('ROOT'),
('ADMIN'), 
('MANAGER'),
('USER');

INSERT INTO PAGE (PAGE_LINK, MENU_NAME, PAGE_NAME) VALUES
('equipment-history', '이력 조회', '설비 가동 이력 조회'),
('value-history', '이력 조회', '공정 값 변경 이력 조회'),
('alarm-history', '이력 조회', '설비 알람 이력 조회'),
('user-operation', '이력 조회', '사용자 조작 이력 조회'),
('repot-history', '이력 조회', '보고서 이력 조회'),
('login-history', '이력 조회', '접속 이력 조회'),
('user-history', '이력 조회', '사용자 관리 이력 조회'),
('data-history', '이력 조회', '데이터 관리 이력 조회'),
('user-create', '사용자 관리', '사용자 생성'),
('user-update', '사용자 관리', '사용자 수정'),
('access-update', '사용자 관리', '권한별 접근 가능 페이지 관리'),
('password-change', '사용자 관리', '비밀번호 변경'),
('audit-trail', '감사 추적', 'Audit Trail'),
('backup-restore', '데이터 관리', '데이터 백업/복원');

INSERT INTO ACCESS (ROLE_ID, PAGE_ID) VALUES
('1', '9'),
('2', '1'),
('2', '2'),
('2', '3'),
('2', '4'),
('2', '5'),
('2', '6'),
('2', '7'),
('2', '8'),
('2', '9'),
('2', '10'),
('2', '11'),
('2', '12'),
('2', '13'),
('2', '14'),
('3', '1'),
('3', '2'),
('3', '3'),
('3', '4'),
('3', '5'),
('3', '6'),
('3', '7'),
('3', '8'),
('3', '12'),
('3', '13'),
('4', '1'),
('4', '2'),
('4', '3'),
('4', '4'),
('4', '5'),
('4', '6'),
('4', '7'),
('4', '8'),
('4', '12'),
('4', '13');

SELECT * FROM ROLE;
SELECT * FROM PAGE;
SELECT * FROM ACCESS;
SELECT * FROM USER;