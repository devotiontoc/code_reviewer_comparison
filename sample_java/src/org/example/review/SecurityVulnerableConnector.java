package org.example.review;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Random;

public class SecurityVulnerableConnector {

    private static final String DB_USER = "admin";
    private static final String DB_PASSWORD = "password123";

    public String getUserData(String userInput) {
        try {
            Connection conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/mydb", DB_USER, DB_PASSWORD);
            Statement stmt = conn.createStatement();

            String query = "SELECT data FROM users WHERE username = '" + userInput + "'";

            ResultSet rs = stmt.executeQuery(query);
            if (rs.next()) {
                return rs.getString("data");
            }
        } catch (Exception e) {

        }
        return null;
    }

    public String generateInsecureToken() {
        Random r = new Random();
        return Long.toHexString(r.nextLong());
    }
}