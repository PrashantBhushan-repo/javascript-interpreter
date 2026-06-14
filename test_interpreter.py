# test_interpreter.py

import unittest
import math
from lexer import Lexer
from parser import Parser
from evaluator import Evaluator
import values

class TestJSInterpreter(unittest.TestCase):
    def eval_js(self, source: str):
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        if parser.errors:
            raise ValueError(f"Syntax Errors: {parser.errors}")
        evaluator = Evaluator()
        return evaluator.evaluate(program, evaluator.global_env)

    def eval_js_with_stdout(self, source: str):
        lexer = Lexer(source)
        parser = Parser(lexer)
        program = parser.parse_program()
        if parser.errors:
            raise ValueError(f"Syntax Errors: {parser.errors}")
        evaluator = Evaluator()
        val = evaluator.evaluate(program, evaluator.global_env)
        return val, evaluator.stdout_buffer

    # --- Variables & Scoping ---

    def test_var_let_const(self):
        # basic let/const/var assignment
        src = """
        let x = 10;
        const y = 20;
        var z = 30;
        x + y + z;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 60.0)

    def test_const_reassignment_fails(self):
        src = """
        const x = 10;
        x = 20;
        """
        with self.assertRaises(TypeError):
            self.eval_js(src)

    def test_block_scope_let(self):
        src = """
        let x = 1;
        {
            let x = 2;
        }
        x;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 1.0)

    def test_block_scope_var_hoisting(self):
        src = """
        {
            var x = 99;
        }
        x;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 99.0)

    def test_shadowing_and_reassignment(self):
        src = """
        let x = 1;
        {
            x = 2;
            let x = 3; // Shadows inner block, but does it error or shadow correctly?
            // Note: in JS, accessing 'x' before declaration inside block is TDZ error.
            // Our environment will let them shadow.
        }
        x;
        """
        # Let's test standard let scoping
        src_standard = """
        let x = 1;
        {
            let x = 2;
            x = 3;
        }
        x;
        """
        res = self.eval_js(src_standard)
        self.assertEqual(res.to_number(), 1.0)

    # --- Control Flow ---

    def test_if_else(self):
        src = """
        let x = 10;
        let result = "";
        if (x > 15) {
            result = "greater";
        } else if (x > 5) {
            result = "medium";
        } else {
            result = "small";
        }
        result;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_string(), "medium")

    def test_while_loop(self):
        src = """
        let count = 0;
        let i = 0;
        while (i < 5) {
            i = i + 1;
            if (i === 3) {
                continue;
            }
            count = count + i;
        }
        count;
        """
        res = self.eval_js(src)
        # 1 + 2 + (skip 3) + 4 + 5 = 12
        self.assertEqual(res.to_number(), 12.0)

    def test_do_while_loop(self):
        src = """
        let i = 0;
        do {
            i = i + 1;
        } while (i < 5);
        i;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 5.0)

    def test_for_loop(self):
        src = """
        let sum = 0;
        for (let i = 0; i < 5; i = i + 1) {
            sum = sum + i;
        }
        sum;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 10.0)

    def test_switch_case(self):
        src = """
        function getVal(x) {
            let res = 0;
            switch(x) {
                case 1:
                    res = 10;
                    break;
                case 2:
                case 3:
                    res = 20; // Fallthrough test
                    break;
                default:
                    res = 99;
            }
            return res;
        }
        [getVal(1), getVal(2), getVal(3), getVal(5)];
        """
        res = self.eval_js(src)
        self.assertTrue(isinstance(res, values.JSArray))
        self.assertEqual(res.elements[0].to_number(), 10.0)
        self.assertEqual(res.elements[1].to_number(), 20.0)
        self.assertEqual(res.elements[2].to_number(), 20.0)
        self.assertEqual(res.elements[3].to_number(), 99.0)

    # --- Functions & Closures ---

    def test_closures(self):
        src = """
        function makeAdder(x) {
            return (y) => x + y;
        }
        let add5 = makeAdder(5);
        add5(10);
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 15.0)

    def test_arrow_functions(self):
        src = """
        const double = x => x * 2;
        const add = (x, y) => { return x + y; };
        double(5) + add(10, 20);
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 40.0)

    def test_rest_parameters(self):
        src = """
        function sumAll(first, ...others) {
            let sum = first;
            for (let i = 0; i < others.length; i = i + 1) {
                sum = sum + others[i];
            }
            return sum;
        }
        sumAll(10, 20, 30, 40);
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 100.0)

    def test_this_preservation(self):
        src = """
        let obj = {
            value: 42,
            getValue: function() {
                return this.value;
            }
        };
        obj.getValue();
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_number(), 42.0)

    # --- Array Operations ---

    def test_array_mutations(self):
        src = """
        let arr = [1, 2];
        arr.push(3, 4); // returns 4
        let popped = arr.pop(); // 4
        let shifted = arr.shift(); // 1
        arr.unshift(99); // returns 3
        [arr, popped, shifted];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[1].to_number(), 4.0)
        self.assertEqual(res.elements[2].to_number(), 1.0)
        arr = res.elements[0]
        self.assertEqual(arr.elements[0].to_number(), 99.0)
        self.assertEqual(arr.elements[1].to_number(), 2.0)
        self.assertEqual(arr.elements[2].to_number(), 3.0)

    def test_array_slice_splice_concat(self):
        src = """
        let arr = [10, 20, 30, 40, 50];
        let sl = arr.slice(1, 4); // [20, 30, 40]
        let spl = arr.splice(2, 2, 99, 100); // deletes [30, 40], inserts 99, 100
        let c = arr.concat([8, 9]); // [10, 20, 99, 100, 50, 8, 9]
        [sl, spl, arr, c];
        """
        res = self.eval_js(src)
        sl = res.elements[0]
        spl = res.elements[1]
        arr = res.elements[2]
        c = res.elements[3]
        
        self.assertEqual(sl.to_string(), "20,30,40")
        self.assertEqual(spl.to_string(), "30,40")
        self.assertEqual(arr.to_string(), "10,20,99,100,50")
        self.assertEqual(c.to_string(), "10,20,99,100,50,8,9")

    def test_array_sort_reverse(self):
        src = """
        let arr = [4, 2, 5, 1, 3];
        arr.sort();
        arr.reverse();
        arr;
        """
        res = self.eval_js(src)
        self.assertEqual(res.to_string(), "5,4,3,2,1")

    def test_array_high_order_methods(self):
        src = """
        let arr = [1, 2, 3, 4];
        let mapped = arr.map(x => x * 10); // [10, 20, 30, 40]
        let filtered = arr.filter(x => x % 2 === 0); // [2, 4]
        let reduced = arr.reduce((acc, x) => acc + x, 100); // 110
        let found = arr.find(x => x > 2); // 3
        let someVal = arr.some(x => x === 4); // true
        let everyVal = arr.every(x => x > 0); // true
        [mapped, filtered, reduced, found, someVal, everyVal];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[0].to_string(), "10,20,30,40")
        self.assertEqual(res.elements[1].to_string(), "2,4")
        self.assertEqual(res.elements[2].to_number(), 110.0)
        self.assertEqual(res.elements[3].to_number(), 3.0)
        self.assertEqual(res.elements[4].to_boolean(), True)
        self.assertEqual(res.elements[5].to_boolean(), True)

    # --- String Operations ---

    def test_string_methods(self):
        src = """
        let str = "  Hello JavaScript World  ";
        let trimmed = str.trim();
        let upper = trimmed.toUpperCase();
        let lower = trimmed.toLowerCase();
        let sub = trimmed.substring(6, 16); // "JavaScript"
        let splitArr = trimmed.split(" "); // ["Hello", "JavaScript", "World"]
        let inc = trimmed.includes("Script");
        let start = trimmed.startsWith("He");
        let end = trimmed.endsWith("ld");
        let idx = trimmed.indexOf("Java");
        let rep = trimmed.replace("World", "Interpreter");
        [trimmed, upper, lower, sub, splitArr, inc, start, end, idx, rep];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[0].to_string(), "Hello JavaScript World")
        self.assertEqual(res.elements[1].to_string(), "HELLO JAVASCRIPT WORLD")
        self.assertEqual(res.elements[2].to_string(), "hello javascript world")
        self.assertEqual(res.elements[3].to_string(), "JavaScript")
        self.assertEqual(res.elements[4].to_string(), "Hello,JavaScript,World")
        self.assertEqual(res.elements[5].to_boolean(), True)
        self.assertEqual(res.elements[6].to_boolean(), True)
        self.assertEqual(res.elements[7].to_boolean(), True)
        self.assertEqual(res.elements[8].to_number(), 6.0)
        self.assertEqual(res.elements[9].to_string(), "Hello JavaScript Interpreter")

    # --- Built-in Objects ---

    def test_math_constants_and_operations(self):
        src = """
        [Math.PI > 3.14, Math.E > 2.7, Math.floor(5.8), Math.abs(-9), Math.pow(2, 3), Math.sqrt(16)];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[0].to_boolean(), True)
        self.assertEqual(res.elements[1].to_boolean(), True)
        self.assertEqual(res.elements[2].to_number(), 5.0)
        self.assertEqual(res.elements[3].to_number(), 9.0)
        self.assertEqual(res.elements[4].to_number(), 8.0)
        self.assertEqual(res.elements[5].to_number(), 4.0)

    def test_date_object(self):
        src = """
        let d = new Date(2026, 5, 14, 17, 30, 0); // Month is 0-indexed, so 5 is June
        [d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes(), d.getSeconds()];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[0].to_number(), 2026.0)
        self.assertEqual(res.elements[1].to_number(), 5.0) # June (0-indexed)
        self.assertEqual(res.elements[2].to_number(), 14.0)
        self.assertEqual(res.elements[3].to_number(), 17.0)
        self.assertEqual(res.elements[4].to_number(), 30.0)
        self.assertEqual(res.elements[5].to_number(), 0.0)

    # --- Operators & Expressions & Coercions ---

    def test_coercions(self):
        # string + number -> concatenation
        res1 = self.eval_js('"5" + 2')
        self.assertEqual(res1.to_string(), "52")
        
        # string - number -> numeric math
        res2 = self.eval_js('"5" - 2')
        self.assertEqual(res2.to_number(), 3.0)

        # loose equality coercions
        self.assertTrue(self.eval_js('"5" == 5').to_boolean())
        self.assertTrue(self.eval_js('true == 1').to_boolean())
        self.assertTrue(self.eval_js('null == undefined').to_boolean())
        
        # strict equality comparisons
        self.assertFalse(self.eval_js('"5" === 5').to_boolean())
        self.assertFalse(self.eval_js('null === undefined').to_boolean())

    def test_spread_operator(self):
        src = """
        let arr1 = [2, 3];
        let arr2 = [1, ...arr1, 4]; // Spread in array literal
        
        function sumThree(x, y, z) {
            return x + y + z;
        }
        let val = sumThree(...arr1, 10); // Spread in call args
        [arr2, val];
        """
        res = self.eval_js(src)
        arr2 = res.elements[0]
        val = res.elements[1]
        self.assertEqual(arr2.to_string(), "1,2,3,4")
        self.assertEqual(val.to_number(), 15.0)

    def test_increment_decrement(self):
        src = """
        let i = 5;
        let a = i++; // a = 5, i = 6
        let b = ++i; // b = 7, i = 7
        let c = i--; // c = 7, i = 6
        let d = --i; // d = 5, i = 5
        [a, b, c, d, i];
        """
        res = self.eval_js(src)
        self.assertEqual(res.elements[0].to_number(), 5.0)
        self.assertEqual(res.elements[1].to_number(), 7.0)
        self.assertEqual(res.elements[2].to_number(), 7.0)
        self.assertEqual(res.elements[3].to_number(), 5.0)
        self.assertEqual(res.elements[4].to_number(), 5.0)

if __name__ == "__main__":
    unittest.main()
