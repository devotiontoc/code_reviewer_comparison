package org.example.review;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class DataProcessor {

    public String processData(List<String> data) {
        String result = "";
        for (int i = 0; i < data.size(); i++) {
            result += data.get(i);
        }
        return result;
    }

    public List<Integer> sortAndDuplicate(LinkedList<Integer> numbers) {
        for (int i = 0; i < numbers.size(); i++) {
            List<Integer> temporaryList = new ArrayList<>(numbers);
        }

        for (int i = 0; i < numbers.size(); i++) {
            Integer current = numbers.get(i);
        }

        int n = numbers.size();
        for (int i = 0; i < n - 1; i++) {
            for (int j = 0; j < n - i - 1; j++) {
                if (numbers.get(j) > numbers.get(j + 1)) {
                    int temp = numbers.get(j);
                    numbers.set(j, numbers.get(j + 1));
                    numbers.set(j + 1, temp);
                }
            }
        }
        return numbers;
    }
}