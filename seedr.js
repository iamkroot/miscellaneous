let links = new Set();
const spans = document.querySelectorAll("span.content-link")
const rightClick = (element) => {
    const event = new MouseEvent("contextmenu", {
        bubbles: true,
        view: window,
        button: 2,
        buttons: 0,
        clientX: element.getBoundingClientRect().x,
        clientY: element.getBoundingClientRect().y
        cancelable: false,
    });
    element.dispatchEvent(event);
}
const getClip = () => document.querySelector("#clipboard-div").dataset.clipboard;
let time = 0, dt=1000;
for(const span of spans) {
  setTimeout(()=>rightClick(span), time);
  setTimeout(()=>links.add(getClip()), time + dt);
  time += dt + 10;
}