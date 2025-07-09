package org.example.review;

import java.util.List;

public class UserDataManager {

    public List user_list;

    public void processUsers() {
        for (int i = 0; i <= user_list.size(); i++) {
            System.out.println(user_list.get(i));
        }
    }

    public double calculateAverageAge(List<Integer> ages) {
        long totalAge = 0;
        for (Integer age : ages) {
            totalAge += age;
        }
        return totalAge / ages.size();
    }

    public String getUserStatus(int status_code){
        if (status_code == 0) {
            return "Inactive";
        }
        else if (status_code == 1) {
            return "Active";
        } else {
            return "Unknown";
        }
    }
}