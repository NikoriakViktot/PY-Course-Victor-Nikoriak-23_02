import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
import sympy as sp
import math

st.set_page_config(page_title="Python Math Lab", layout="centered")

st.title("🧪 Python Math Lab")
st.subheader("📱 iPhone Calculator")

st.caption("Interactive calculator styled like iOS")
components.html("""
<style>

body{
background:#000;
display:flex;
justify-content:center;
font-family:sans-serif;
}

.calc{
width:320px;
}

.display{
height:80px;
color:white;
font-size:48px;
text-align:right;
padding:10px;
}

.grid{
display:grid;
grid-template-columns:repeat(4,1fr);
gap:10px;
}

button{
height:70px;
border-radius:50%;
border:none;
font-size:24px;
}

.num{
background:#333;
color:white;
}

.op{
background:#ff9500;
color:white;
}

.fn{
background:#a5a5a5;
color:black;
}

.zero{
grid-column:span 2;
border-radius:40px;
text-align:left;
padding-left:25px;
}

</style>

<div class="calc">

<div id="display" class="display">0</div>

<div class="grid">

<button class="fn" onclick="press('AC')">AC</button>
<button class="fn" onclick="press('del')">⌫</button>
<button class="fn" onclick="press('π')">π</button>
<button class="op" onclick="press('/')">÷</button>

<button class="num" onclick="press('7')">7</button>
<button class="num" onclick="press('8')">8</button>
<button class="num" onclick="press('9')">9</button>
<button class="op" onclick="press('*')">×</button>

<button class="num" onclick="press('4')">4</button>
<button class="num" onclick="press('5')">5</button>
<button class="num" onclick="press('6')">6</button>
<button class="op" onclick="press('-')">−</button>

<button class="num" onclick="press('1')">1</button>
<button class="num" onclick="press('2')">2</button>
<button class="num" onclick="press('3')">3</button>
<button class="op" onclick="press('+')">+</button>

<button class="num zero" onclick="press('0')">0</button>
<button class="num" onclick="press('.')">.</button>
<button class="op" onclick="press('=')">=</button>

</div>
</div>

<script>

let expr=""

function press(x){

if(x==="AC"){
expr=""
update()
return
}

if(x==="del"){
expr=expr.slice(0,-1)
update()
return
}

if(x==="="){
calculate()
return
}

if(x==="π"){
expr+=Math.PI
}
else{
expr+=x
}

update()
}

function calculate(){

try{
expr=eval(expr).toString()
}
catch{
expr="Error"
}

update()
}

function update(){

document.getElementById("display").innerText=expr || "0"

}

/* ===== KEYBOARD SUPPORT ===== */

document.addEventListener("keydown", function(e){

let k = e.key

if("0123456789".includes(k)){
expr += k
update()
}

else if(["+","-","*","/","."].includes(k)){
expr += k
update()
}

else if(k === "Enter"){
calculate()
}

else if(k === "Backspace"){
expr = expr.slice(0,-1)
update()
}

})

</script>
""", height=500)

tab_graph, tab_deriv, tab_integral = st.tabs(
    [ "📊 Graph", "🧠 Derivative", "∫ Integral"]
)


# ============================================================
# 📊 GRAPH
# ============================================================

with tab_graph:

    st.subheader("📊 Function Plotter")

    functions = {
        "sin(x)": "np.sin(x)",
        "cos(x)": "np.cos(x)",
        "tan(x)": "np.tan(x)",
        "x²": "x**2",
        "x³": "x**3",
        "√x": "np.sqrt(np.abs(x))",
        "exp(x)": "np.exp(x)",
        "log(x)": "np.log(np.abs(x)+1e-6)",
        "1/x": "1/(x+1e-6)",
        "|x|": "np.abs(x)"
    }

    selected = st.selectbox("Choose function", list(functions.keys()))

    func = functions[selected]

    x = np.linspace(-10,10,400)

    try:
        y = eval(func)

        fig, ax = plt.subplots()

        ax.plot(x,y)

        ax.axhline(0)
        ax.axvline(0)

        ax.grid(True)

        ax.set_title(selected)

        st.pyplot(fig)

    except:
        st.error("Invalid function")


# ============================================================
# 🧠 DERIVATIVE
# ============================================================

with tab_deriv:

    st.subheader("🧠 Derivative Calculator")

    x = sp.symbols('x')

    expr = st.text_input("Function", "x**3 + 2*x")

    try:

        f = sp.sympify(expr)

        derivative = sp.diff(f,x)

        st.write("Function:")
        st.latex(sp.latex(f))

        st.write("Derivative:")
        st.latex(sp.latex(derivative))

        xs = np.linspace(-10,10,200)

        f_num = sp.lambdify(x,f,"numpy")
        d_num = sp.lambdify(x,derivative,"numpy")

        fig,ax = plt.subplots()

        ax.plot(xs,f_num(xs),label="f(x)")
        ax.plot(xs,d_num(xs),label="f'(x)")

        ax.legend()
        ax.grid(True)

        st.pyplot(fig)

    except:
        st.error("Invalid expression")


# ============================================================
# ∫ INTEGRAL
# ============================================================

with tab_integral:

    st.subheader("∫ Integral Calculator")

    x = sp.symbols('x')

    expr = st.text_input("Function to integrate", "x**2")

    try:

        f = sp.sympify(expr)

        integral = sp.integrate(f,x)

        st.write("Integral:")
        st.latex(sp.latex(integral))

    except:
        st.error("Invalid expression")