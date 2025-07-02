-- DROP TABLE IF EXISTS answer;
-- DROP TABLE IF EXISTS question;
-- DROP TABLE IF EXISTS user;
-- DROP TABLE IF EXISTS board;

CREATE TABLE board (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    create_date DATETIME NOT NULL
);

CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(200) NOT NULL,
    realname VARCHAR(100) NOT NULL,
    company VARCHAR(255) DEFAULT '무직',
    email VARCHAR(255)
);

CREATE TABLE question (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    create_date DATETIME NOT NULL,
    user_id INT NOT NULL,
    board_id INT NOT NULL,
    is_secret BOOLEAN DEFAULT FALSE,
    secret_pw VARCHAR(200),
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (board_id) REFERENCES board(id)
);

CREATE TABLE answer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    create_date DATETIME NOT NULL,
    user_id INT NOT NULL,
    question_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (question_id) REFERENCES question(id)
);