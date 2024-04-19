CREATE TABLE IF NOT EXISTS Users (
                                     user_name text NOT NULL PRIMARY KEY,
                                     password text,
                                     role text
);
INSERT INTO Users (user_name, password, role) VALUES ( 'admin', 'admin', 'admin' )
