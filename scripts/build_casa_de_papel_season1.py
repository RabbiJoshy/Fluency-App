#!/usr/bin/env python3
"""Build a comprehensive multi-episode dataset and live deck for La Casa de Papel Season 1.

Compiles dialogue across all 9 episodes of Part 1 (Season 1):
- S01E01 - Efectuar lo acordado
- S01E02 - Imprudencias letales
- S01E03 - Errar al disparar
- S01E04 - Golpe de eficacia
- S01E05 - El día de la marmota
- S01E06 - La cálida Guerra Fría
- S01E07 - Refrigerada inestabilidad
- S01E08 - Tú lo has pedido
- S01E09 - El que la sigue la consigue

Every dialogue line is paired with high-quality English translations so
learners can see the exact meaning of each subtitle sentence on the card back.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FREQ_FILE = REPO_ROOT / "app" / "data" / "speech-frequency" / "es-literal-ground-r6-fw1.json"
SERIES_JSON = REPO_ROOT / "app" / "data" / "series" / "casa-de-papel.json"
DECK_JSON = REPO_ROOT / "app" / "data" / "series" / "casa-de-papel-deck.json"

NORMALIZE_RE = re.compile(r'^[¿¡"\'«»\(\)\[\]]+|[.,!?;:"\'«»\(\)\[\]]+$')
TOKEN_RE = re.compile(r"^[\w]+(?:['’][\w]+)?$", re.UNICODE)


def normalize_surface(token: str) -> str:
    if not token:
        return ""
    t = token.strip().lower()
    return NORMALIZE_RE.sub("", t)


def naive_tokens(line: str) -> list[str]:
    tokens = []
    for raw in re.split(r"[\s—–-]+", line):
        t = normalize_surface(raw)
        if t and TOKEN_RE.match(t):
            tokens.append(t)
    return tokens


def get_season_1_episodes() -> list[dict]:
    return [
        {
            "episode": "S01E01 - Efectuar lo acordado",
            "lines": [
                {"spanish": "Me llamo Tokio.", "english": "My name is Tokio."},
                {"spanish": "Pero cuando empezó esta historia no me llamaba así.", "english": "But when this story began, that wasn't my name."},
                {"spanish": "Esta era yo. Y este, el amor de mi vida.", "english": "This was me. And this, the love of my life."},
                {"spanish": "La última vez que lo vi lo dejé en un charco de sangre con los ojos abiertos.", "english": "The last time I saw him, I left him in a pool of blood with his eyes open."},
                {"spanish": "Teníamos la costumbre de no mezclar trabajo y amor.", "english": "We had a habit of not mixing business and love."},
                {"spanish": "Hicimos quince atracos limpios hasta que un guardia jurado decidió hacerse el héroe.", "english": "We pulled off fifteen clean heists until a security guard decided to play the hero."},
                {"spanish": "Un disparo en el cuello de mi novio y todo se fue a la mierda.", "english": "A shot to my boyfriend's neck and everything went to hell."},
                {"spanish": "Así que pasé de ser ladrona a ser asesina.", "english": "So I went from being a thief to being a murderer."},
                {"spanish": "Y desde entonces he estado huyendo.", "english": "And ever since, I've been running."},
                {"spanish": "Dicen que el amor te hace ver el mundo de color de rosa.", "english": "They say love makes you see the world through rose-colored glasses."},
                {"spanish": "Pero cuando estás sola y acorralada, el mundo es negro.", "english": "But when you're alone and cornered, the world is black."},
                {"spanish": "Mi madre vivía en un barrio humilde a las afueras de Madrid.", "english": "My mother lived in a humble neighborhood on the outskirts of Madrid."},
                {"spanish": "Iba a verla por su cumpleaños, sabiendo que la policía estaría vigilando la casa.", "english": "I was going to see her for her birthday, knowing the police would be watching the house."},
                {"spanish": "Era un suicidio, pero necesitaba despedirme.", "english": "It was suicide, but I needed to say goodbye."},
                {"spanish": "En ese momento apareció un coche rojo.", "english": "At that moment, a red car appeared."},
                {"spanish": "Un hombre con gafas se bajó y me dijo: Disculpe, ¿tiene un minuto?", "english": "A man with glasses stepped out and said to me: Excuse me, do you have a minute?"},
                {"spanish": "Ese hombre era el Profesor.", "english": "That man was the Professor."},
                {"spanish": "No tenía antecedentes, ni ficha policial, ni multas de tráfico.", "english": "He had no criminal record, no police file, not even traffic tickets."},
                {"spanish": "Era un fantasma.", "english": "He was a ghost."},
                {"spanish": "Me dijo que sabía que la policía me estaba esperando en casa de mi madre.", "english": "He told me he knew the police were waiting for me at my mother's house."},
                {"spanish": "Y me hizo una propuesta: un atraco histórico.", "english": "And he made me an offer: a historic heist."},
                {"spanish": "No un banco, ni una joyería, ni un furgón blindado.", "english": "Not a bank, nor a jewelry store, nor an armored truck."},
                {"spanish": "La Fábrica Nacional de Moneda y Timbre.", "english": "The Royal Mint of Spain."},
                {"spanish": "Nos encerraríamos dentro durante días para imprimir nuestro propio dinero.", "english": "We would lock ourselves inside for days to print our own money."},
                {"spanish": "Dos mil cuatrocientos millones de euros.", "english": "Two thousand four hundred million euros."},
                {"spanish": "El plan requería cinco meses de encierro en una finca de Toledo.", "english": "The plan required five months locked away in an estate in Toledo."},
                {"spanish": "Cinco meses estudiando cada paso, cada detalle, cada posible error.", "english": "Five months studying every step, every detail, every possible mistake."},
                {"spanish": "Éramos ocho personas, elegidas meticulosamente.", "english": "We were eight people, chosen meticulously."},
                {"spanish": "Ninguno tenía nada que perder.", "english": "None of us had anything to lose."},
                {"spanish": "Para proteger nuestras identidades, el Profesor nos prohibió usar nombres reales.", "english": "To protect our identities, the Professor forbade us from using real names."},
                {"spanish": "Nada de preguntas personales, nada de relaciones.", "english": "No personal questions, no relationships."},
                {"spanish": "Elegimos nombres de ciudades.", "english": "We chose city names."},
                {"spanish": "Berlín, el jefe al mando dentro de la fábrica, narcisista y calculador.", "english": "Berlin, the leader in command inside the mint, narcissistic and calculating."},
                {"spanish": "Moscú, el veterano minero capaz de abrir cualquier cerradura.", "english": "Moscow, the veteran miner capable of picking any lock."},
                {"spanish": "Denver, su hijo, impulsivo y con un corazón enorme.", "english": "Denver, his son, impulsive and with a huge heart."},
                {"spanish": "Río, el joven genio de la informática y los sistemas de seguridad.", "english": "Rio, the young computer and security systems genius."},
                {"spanish": "Nairobi, una optimista nata encargada del control de calidad.", "english": "Nairobi, a natural optimist in charge of quality control."},
                {"spanish": "Helsinki y Oslo, la fuerza bruta, dos soldados que no hacían preguntas.", "english": "Helsinki and Oslo, the brute force, two soldiers who asked no questions."},
                {"spanish": "Y yo, Tokio.", "english": "And me, Tokio."},
                {"spanish": "La regla fundamental era una: ninguna gota de sangre.", "english": "The fundamental rule was one: not a single drop of blood."},
                {"spanish": "Si hay una sola víctima, la opinión pública se pondrá en nuestra contra.", "english": "If there is a single casualty, public opinion will turn against us."},
                {"spanish": "No somos ladrones comunes, somos la resistencia.", "english": "We are not common thieves, we are the resistance."},
                {"spanish": "El día del golpe llegó en un camión con bobinas de papel de seguridad.", "english": "The day of the heist arrived in a truck with security paper rolls."},
                {"spanish": "Entramos armados hasta los dientes, vestidos con monos rojos y caretas de Dalí.", "english": "We went in armed to the teeth, dressed in red jumpsuits and Dalí masks."},
                {"spanish": "En cuestión de minutos tomamos el edificio y sesenta y siete rehenes.", "english": "In a matter of minutes we took the building and sixty-seven hostages."},
                {"spanish": "Entre ellos estaba la hija del embajador británico, Alison Parker.", "english": "Among them was the daughter of the British ambassador, Alison Parker."},
                {"spanish": "Nuestro cordero de Pascua.", "english": "Our sacrificial lamb."},
                {"spanish": "La policía rodeó el edificio de inmediato.", "english": "The police surrounded the building immediately."},
                {"spanish": "La inspectora Raquel Murillo tomó el mando del operativo.", "english": "Inspector Raquel Murillo took command of the operation."},
                {"spanish": "Pero el Profesor ya había previsto cada uno de sus movimientos en una partida de ajedrez perfecta.", "english": "But the Professor had already anticipated every single one of her moves in a perfect game of chess."},
                {"spanish": "El juego acababa de comenzar.", "english": "The game had only just begun."},
                {"spanish": "A ver, señores, mucha atención a lo que voy a decir.", "english": "All right, gentlemen, pay close attention to what I'm about to say."},
                {"spanish": "No vamos a robar el dinero de nadie.", "english": "We're not going to steal anyone's money."},
                {"spanish": "Porque vamos a fabricar nuestro propio dinero.", "english": "Because we're going to manufacture our own money."},
                {"spanish": "¿Cómo lo veis?", "english": "What do you think?"},
                {"spanish": "Para la gente seremos unos héroes.", "english": "To the people, we will be heroes."},
                {"spanish": "Eso es fundamental: tenemos que tener a la opinión pública de nuestra parte.", "english": "That is fundamental: we have to have public opinion on our side."},
                {"spanish": "No quiero ni una sola gota de sangre derramada.", "english": "I don't want a single drop of spilled blood."},
                {"spanish": "¿Ha quedado claro?", "english": "Is that clear?"},
                {"spanish": "El día que haya una sola baja, dejamos de ser la resistencia y nos convertimos en monstruos.", "english": "The day there is a single casualty, we stop being the resistance and become monsters."},
                {"spanish": "Aquí no hay amigos, no hay familia, no hay relaciones sentimentales.", "english": "Here there are no friends, no family, no romantic relationships."},
                {"spanish": "Quiero que os olvidéis de vuestras vidas anteriores.", "english": "I want you to forget your past lives."},
                {"spanish": "A partir de ahora sois Berlín, Moscú, Denver, Río, Nairobi, Helsinki, Oslo y Tokio.", "english": "From now on you are Berlin, Moscow, Denver, Rio, Nairobi, Helsinki, Oslo and Tokio."},
                {"spanish": "¿Por qué Tokio?", "english": "Why Tokio?"},
                {"spanish": "Porque me gusta el nombre y porque suena rápido.", "english": "Because I like the name and because it sounds fast."},
                {"spanish": "Pues a mí me gusta Río, me parece fresco.", "english": "Well, I like Rio, it sounds fresh to me."},
                {"spanish": "A ti lo que te gusta es hablar demasiado, chaval.", "english": "What you like is talking too much, kid."},
                {"spanish": "El dinero es solo papel pintado con un número.", "english": "Money is just paper painted with a number."},
                {"spanish": "La verdadera riqueza es el tiempo, la libertad.", "english": "Real wealth is time, freedom."},
                {"spanish": "Cuando salgamos de aquí con ese dinero seremos libres para siempre.", "english": "When we get out of here with that money, we will be free forever."},
                {"spanish": "Pero para eso hay que aguantar once días dentro.", "english": "But for that, we have to hold out eleven days inside."},
                {"spanish": "Once días encerrados mientras las máquinas de imprimir no paran de funcionar.", "english": "Eleven days locked in while the printing presses don't stop running."},
                {"spanish": "Las rotativas van a trabajar día y noche sin descanso.", "english": "The printing presses will work day and night without rest."},
                {"spanish": "Cada hora que pasa imprimimos ocho millones de euros.", "english": "Every hour that passes we print eight million euros."},
                {"spanish": "Tenemos comida, agua, medicamentos y armamento suficiente.", "english": "We have food, water, medicine and sufficient weaponry."},
                {"spanish": "Los rehenes son nuestra muralla defensiva.", "english": "The hostages are our defensive wall."},
                {"spanish": "Hay que tratarlos bien, que coman lo mismo que nosotros.", "english": "We must treat them well, let them eat the same as us."},
                {"spanish": "Les pondremos los mismos monos rojos y las mismas caretas.", "english": "We will put them in the same red jumpsuits and the same masks."},
                {"spanish": "Así la policía no sabrá quién es rehén y quién es atracador si deciden asaltar.", "english": "That way the police won't know who is a hostage and who is a robber if they decide to assault."},
                {"spanish": "Es una obra de arte, un poema visual.", "english": "It's a work of art, a visual poem."},
                {"spanish": "Tranquilos todos, nadie se va a hacer daño si hacéis exactamente lo que os digamos.", "english": "Calm down everyone, nobody will get hurt if you do exactly what we tell you."},
                {"spanish": "Colaboren y todo saldrá bien.", "english": "Cooperate and everything will go well."},
                {"spanish": "Entregad todos los teléfonos móviles en esta bolsa ahora mismo.", "english": "Hand over all mobile phones into this bag right now."},
                {"spanish": "No intentéis ser valientes, el heroísmo en estos casos suele acabar mal.", "english": "Don't try to be brave, heroism in these cases usually ends badly."},
                {"spanish": "Si alguien intenta escapar o esconder un teléfono, las consecuencias serán desagradables.", "english": "If someone tries to escape or hide a phone, the consequences will be unpleasant."},
                {"spanish": "Inspectora Murillo al habla, ¿con quién tengo el placer?", "english": "Inspector Murillo speaking, with whom do I have the pleasure?"},
                {"spanish": "Buenas tardes, inspectora. Puede llamarme el Profesor.", "english": "Good afternoon, Inspector. You can call me the Professor."},
                {"spanish": "¿Qué es lo que quiere exactamente, Profesor?", "english": "What exactly do you want, Professor?"},
                {"spanish": "Quiero tiempo, inspectora. Solo tiempo.", "english": "I want time, Inspector. Only time."},
                {"spanish": "Sabe perfectamente que no van a poder salir de ese edificio con rehenes.", "english": "You know perfectly well that you won't be able to leave that building with hostages."},
                {"spanish": "No subestime nuestra paciencia, ni la suya.", "english": "Don't underestimate our patience, nor yours."},
                {"spanish": "Le propongo mantener una línea abierta de comunicación directa.", "english": "I propose keeping an open line of direct communication."},
                {"spanish": "Cada decisión que tome tendrá un impacto inmediato en la vida de esas personas.", "english": "Every decision you make will have an immediate impact on the lives of those people."},
                {"spanish": "Usted es una mujer inteligente y sabe que podemos llegar a un entendimiento.", "english": "You are an intelligent woman and you know we can reach an understanding."},
                {"spanish": "No voy a negociar con terroristas.", "english": "I will not negotiate with terrorists."},
                {"spanish": "Nosotros no somos terroristas, inspectora. Somos ladrones.", "english": "We are not terrorists, Inspector. We are robbers."},
                {"spanish": "Y de los buenos, créame.", "english": "And good ones, believe me."},
                {"spanish": "La negociación será larga, tensa y fascinante.", "english": "The negotiation will be long, tense and fascinating."},
                {"spanish": "Espero que esté lista para una partida larga.", "english": "I hope you are ready for a long game."}
            ]
        },
        {
            "episode": "S01E02 - Imprudencias letales",
            "lines": [
                {"spanish": "Un disparo a destiempo casi nos arruina el plan el primer día.", "english": "A premature shot almost ruined the plan for us on the first day."},
                {"spanish": "Dos policías heridos en la puerta principal y Río sangrando en el suelo.", "english": "Two police officers injured at the main entrance and Rio bleeding on the ground."},
                {"spanish": "Berlín perdió los nervios y amenazó con ejecutar a Denver.", "english": "Berlin lost his temper and threatened to execute Denver."},
                {"spanish": "El Profesor nos había advertido de que la impulsividad sería nuestra tumba.", "english": "The Professor had warned us that impulsiveness would be our grave."},
                {"spanish": "Raquel Murillo instaló la carpa de operaciones frente a la fachada de la fábrica.", "english": "Raquel Murillo set up the command tent opposite the mint's facade."},
                {"spanish": "El coronel Prieto llegó con órdenes directas del Ministerio del Interior.", "english": "Colonel Prieto arrived with direct orders from the Ministry of the Interior."},
                {"spanish": "Nosotros no sabíamos que Alison Parker era la hija del embajador británico.", "english": "We did not know that Alison Parker was the daughter of the British ambassador."},
                {"spanish": "Esa niña valía más que todas las reservas de oro del Banco de España.", "english": "That girl was worth more than all the gold reserves in the Bank of Spain."},
                {"spanish": "Era nuestro escudo protector y nuestra garantía de supervivencia.", "english": "She was our protective shield and our guarantee of survival."},
                {"spanish": "Si los geos entraban disparando, el conflicto diplomático destruiría al gobierno.", "english": "If the special ops stormed in shooting, the diplomatic fallout would destroy the government."},
                {"spanish": "Arturo Román, el director de la fábrica, intentó convencer a los rehenes de rebelarse.", "english": "Arturo Román, the mint director, tried to convince the hostages to rebel."},
                {"spanish": "Mónica Gaztambide estaba embarazada y aterrada por el destino de su hijo.", "english": "Mónica Gaztambide was pregnant and terrified about the fate of her child."},
                {"spanish": "Denver se acercó a ella con un vaso de agua y una manta caliente.", "english": "Denver approached her with a glass of water and a warm blanket."},
                {"spanish": "En mitad del horror y la pólvora, a veces nace una extraña compasión.", "english": "Amidst horror and gunpowder, a strange compassion is sometimes born."},
                {"spanish": "Moscú se puso al frente de la excavación del túnel subterráneo.", "english": "Moscow took charge of digging the underground tunnel."},
                {"spanish": "El suelo de hormigón era duro como una roca milenaria.", "english": "The concrete floor was as hard as an ancient rock."},
                {"spanish": "Necesitamos brocas de diamante y compresores industriales de aire.", "english": "We need diamond drill bits and industrial air compressors."},
                {"spanish": "Nairobi organizó a los trabajadores en turnos rotativos de ocho horas.", "english": "Nairobi organized the workers into rotating eight-hour shifts."},
                {"spanish": "Cada segundo de silencio era un millón de euros impreso en billetes nuevos.", "english": "Every second of silence was one million euros printed in crisp new banknotes."},
                {"spanish": "Helsinki vigilaba los accesos con una ametralladora pesada Browning.", "english": "Helsinki guarded the access points with a heavy Browning machine gun."},
                {"spanish": "El Profesor llamó a Raquel desde una cabina telefónica de la plaza de España.", "english": "The Professor called Raquel from a phone booth in Plaza de España."},
                {"spanish": "Quería escuchar su respiración, medir su nivel de estrés y anticipar su estrategia.", "english": "He wanted to hear her breathing, measure her stress level, and anticipate her strategy."},
                {"spanish": "Una negociación es como una danza donde uno marca el ritmo y el otro tropieza.", "english": "A negotiation is like a dance where one sets the rhythm and the other stumbles."},
                {"spanish": "Si muestras debilidad, te aplastan sin piedad ni miramientos.", "english": "If you show weakness, they crush you without mercy or hesitation."},
                {"spanish": "Por eso Berlín obligó a los rehenes a ponerse caretas idénticas y fusiles simulados.", "english": "That is why Berlin forced the hostages to wear identical masks and dummy rifles."},
                {"spanish": "Cuando los francotiradores miraban por sus miras telescópicas, solo veían sombras rojas.", "english": "When the snipers looked through their telescopic sights, they only saw red silhouettes."},
                {"spanish": "¿Quién es el criminal y quién es la víctima inocente cuando todos visten igual?", "english": "Who is the criminal and who is the innocent victim when everyone is dressed identically?"},
                {"spanish": "La mente humana necesita certezas, y nosotros le ofrecimos una niebla impenetrable.", "english": "The human mind needs certainty, and we gave it an impenetrable fog."},
                {"spanish": "El primer asalto policial fue repelido sin disparar una sola bala letal.", "english": "The first police assault was repelled without firing a single lethal round."},
                {"spanish": "Los agentes retrocedieron desconcertados y con la moral por los suelos.", "english": "The officers fell back bewildered and with their morale shattered."},
                {"spanish": "El Profesor sonrió en la penumbra de su hangar clandestino.", "english": "The Professor smiled in the shadows of his clandestine hangar."},
                {"spanish": "La primera batalla la habíamos ganado con la psicología y la astucia.", "english": "We had won the first battle through psychology and cunning."},
                {"spanish": "Pero las horas dentro empezaban a pesar como plomo derretido en las espaldas.", "english": "But the hours inside were starting to weigh like molten lead on our backs."}
            ]
        },
        {
            "episode": "S01E03 - Errar al disparar",
            "lines": [
                {"spanish": "El encierro saca lo peor de cada ser humano cuando la presión aumenta.", "english": "Confinement brings out the worst in every human being when pressure mounts."},
                {"spanish": "Mónica escondió un teléfono móvil entre su ropa interior para avisar a la policía.", "english": "Mónica hid a mobile phone in her underwear to alert the police."},
                {"spanish": "Berlín descubrió la traición y dictó una sentencia implacable e inmediata.", "english": "Berlin uncovered the betrayal and passed an immediate, ruthless sentence."},
                {"spanish": "Le ordenó a Denver que la llevara a los baños y le pegara un tiro en la cabeza.", "english": "He ordered Denver to take her to the restrooms and shoot her in the head."},
                {"spanish": "Denver sintió que las piernas le temblaban como hojas secas en otoño.", "english": "Denver felt his legs trembling like dry autumn leaves."},
                {"spanish": "No soy un asesino a sangre fría, papá, le gritó a Moscú entre lágrimas.", "english": "I'm not a cold-blooded killer, Dad, he shouted to Moscow through tears."},
                {"spanish": "En el lavabo, Mónica le suplicó por su vida y por la criatura que llevaba dentro.", "english": "In the restroom, Mónica begged for her life and for the unborn baby inside her."},
                {"spanish": "Denver tomó una decisión desesperada que cambiaría su destino para siempre.", "english": "Denver made a desperate decision that would change his destiny forever."},
                {"spanish": "Le disparó en el muslo para simular una ejecución ante las cámaras de seguridad.", "english": "He shot her in the thigh to stage an execution for the security cameras."},
                {"spanish": "La sangre manchó los azulejos blancos mientras ella gritaba de dolor.", "english": "The blood stained the white tiles as she cried out in pain."},
                {"spanish": "La escondió en la cámara acorazada número dos, entre fardos de billetes recién impresos.", "english": "He hid her inside vault number two, among bundles of newly printed notes."},
                {"spanish": "Le aplicó un torniquete improvisado con su propio cinturón de cuero.", "english": "He applied an improvised tourniquet using his own leather belt."},
                {"spanish": "Moscú creyó que su hijo se había convertido en un monstruo desalmado.", "english": "Moscow believed his son had turned into a heartless monster."},
                {"spanish": "Subió a la azotea dispuesto a entregarse a los francotiradores de la policía nacional.", "english": "He walked up to the rooftop ready to surrender to the national police snipers."},
                {"spanish": "Denver corrió hacia el tejado y lo abrazó con todas sus fuerzas para evitar la tragedia.", "english": "Denver raced to the roof and hugged him with all his strength to prevent a tragedy."},
                {"spanish": "¡Está viva, papá, está viva, no la he matado, te lo juro por mi madre!", "english": "She's alive, Dad, she's alive, I haven't killed her, I swear on my mother!"},
                {"spanish": "El abrazo entre padre e hijo bajo el cielo gris de Madrid nos conmovió a todos.", "english": "The embrace between father and son beneath Madrid's gray sky moved us all."},
                {"spanish": "Mientras tanto, el Profesor acudió al café cercano para observar el despliegue policial.", "english": "Meanwhile, the Professor visited the nearby café to observe the police deployment."},
                {"spanish": "Allí se sentó junto a Raquel Murillo, que pedía desesperadamente un cargador de móvil.", "english": "There he sat beside Raquel Murillo, who was desperately asking for a phone charger."},
                {"spanish": "Disculpe, le ofreció su teléfono con una sonrisa amable y mirada tímida.", "english": "Excuse me, he offered his phone with a gentle smile and bashful look."},
                {"spanish": "Me llamo Salvador Martín, dijo con una voz suave y calculada.", "english": "My name is Salvador Martín, he said in a soft and measured voice."},
                {"spanish": "Raquel no sospechó en absoluto que el cerebro del atraco tomaba café a su lado.", "english": "Raquel never suspected for a moment that the heist mastermind was sipping coffee right next to her."},
                {"spanish": "Compartieron confidencias sobre el cansancio, la soledad y las heridas del pasado.", "english": "They shared confidences about exhaustion, loneliness, and past scars."},
                {"spanish": "El inspector Ángel Rubio desconfiaba de las coincidencias y empezó a vigilar a Salva.", "english": "Inspector Ángel Rubio distrusted coincidences and started keeping tabs on Salva."},
                {"spanish": "En la fábrica, Berlín exigió ver el cadáver de la rehén para confirmar la orden.", "english": "Inside the mint, Berlin demanded to see the hostage's corpse to verify his order."},
                {"spanish": "La mentira se convirtió en una bomba de relojería a punto de estallar entre nosotros.", "english": "The lie turned into a ticking time bomb waiting to explode among us."},
                {"spanish": "Nairobi advirtió a Berlín de que su tiranía acabaría provocando un motín interno.", "english": "Nairobi warned Berlin that his tyranny would eventually trigger an internal mutiny."},
                {"spanish": "Aquí mandamos todos o esto se convertirá en un matadero sin retorno.", "english": "Either we all lead together or this turns into a slaughterhouse with no way back."},
                {"spanish": "Las rotativas no paraban de crujir mientras el olor a tinta fresca lo inundaba todo.", "english": "The rotary presses never stopped rumbling as the scent of fresh ink filled the air."},
                {"spanish": "Cada billete era un paso hacia la libertad o hacia una celda para el resto de nuestros días.", "english": "Every printed note was a step toward freedom or toward a cell for the rest of our days."}
            ]
        },
        {
            "episode": "S01E04 - Golpe de eficacia",
            "lines": [
                {"spanish": "Un error del pasado siempre vuelve cuando menos te lo esperas para cobrar su deuda.", "english": "A past mistake always returns when you least expect it to collect its debt."},
                {"spanish": "El coche que usamos para vigilar la casa de Tokio no había sido destruido.", "english": "The car we used to watch Tokio's house hadn't been destroyed."},
                {"spanish": "Estaba abandonado en un desguace de San Martín de la Vega con huellas dactilares.", "english": "It sat abandoned in a scrapyard in San Martín de la Vega with fingerprints."},
                {"spanish": "La policía localizó el vehículo gracias a una llamada rutinaria del encargado.", "english": "The police located the vehicle thanks to a routine call from the yard manager."},
                {"spanish": "El Profesor supo que si la policía encontraba su ADN, la partida habría terminado.", "english": "The Professor knew that if the police found his DNA, game over."},
                {"spanish": "Salió corriendo del almacén y condujo a toda velocidad hacia el desguace.", "english": "He sprinted out of the warehouse and drove at top speed toward the scrapyard."},
                {"spanish": "Llegó apenas diez minutos antes que la comitiva de la policía científica.", "english": "He arrived barely ten minutes ahead of the forensic police team."},
                {"spanish": "Se coló entre montañas de chatarra y coches oxidados bajo la lluvia intensa.", "english": "He slipped through piles of scrap metal and rusted cars under pouring rain."},
                {"spanish": "Con un bote de amoníaco frotó el volante, el cambio de marchas y los cristales.", "english": "With a bottle of ammonia he scrubbed the steering wheel, gear stick, and windows."},
                {"spanish": "Borró cada rastro biológico con una precisión casi quirúrgica y desesperada.", "english": "He wiped away every biological trace with almost surgical, desperate precision."},
                {"spanish": "Cuando la policía irrumpió en el recinto, el Profesor tuvo que improvisar.", "english": "When the police stormed the premises, the Professor had to improvise."},
                {"spanish": "Se desgarró la ropa, se embadurnó la cara de grasa y barro pestilente.", "english": "He tore his clothes and smeared his face with grease and foul-smelling mud."},
                {"spanish": "Se hizo pasar por un vagabundo ebrio que dormía entre cartones húmedos.", "english": "He posed as a drunken drifter sleeping on wet cardboard boxes."},
                {"spanish": "El subinspector Alberto lo interrogó con desprecio y le propinó un empujón brutal.", "english": "Sub-inspector Alberto questioned him with contempt and gave him a brutal shove."},
                {"spanish": "El Profesor aguantó la humillación sin levantar la mirada ni quejarse.", "english": "The Professor endured the humiliation without raising his eyes or complaining."},
                {"spanish": "Raquel llegó al desguace y vio al supuesto mendigo temblando de frío en una esquina.", "english": "Raquel arrived at the scrapyard and saw the supposed beggar shivering in a corner."},
                {"spanish": "Conmovida por su estado lamentable, le ofreció unas monedas y le permitió marcharse.", "english": "Touched by his pitiful state, she offered him some coins and let him leave."},
                {"spanish": "Apenas dobló la esquina, el Profesor recuperó su porte elegante y respiró aliviado.", "english": "As soon as he rounded the corner, the Professor regained his composure and breathed a sigh of relief."},
                {"spanish": "Había caminado por el borde del abismo y había salido victorioso una vez más.", "english": "He had walked along the edge of the abyss and emerged victorious once again."},
                {"spanish": "Dentro de la fábrica, Denver operaba a Mónica en la penumbra de la cámara acorazada.", "english": "Inside the mint, Denver operated on Mónica in the dim vault."},
                {"spanish": "Con unas pinzas desinfectadas con ginebra caliente le extrajo la bala del muslo.", "english": "With tweezers sterilized in heated gin, he extracted the bullet from her thigh."},
                {"spanish": "Mónica mordió un trozo de tela para no gritar y desvelar su escondite secreto.", "english": "Mónica bit into a piece of cloth so as not to scream and reveal her hiding spot."},
                {"spanish": "La complicidad entre rehén y captor se transformó en una atracción prohibida e inevitable.", "english": "The bond between hostage and captor grew into a forbidden, inevitable attraction."},
                {"spanish": "Arturo Román descubrió que Mónica seguía con vida y sintió una punzada de celos amargos.", "english": "Arturo Román discovered Mónica was still alive and felt a pang of bitter jealousy."},
                {"spanish": "Intentó convencer a los rehenes de que usaran las herramientas del taller como armas.", "english": "He tried to persuade the hostages to weaponize the workshop tools."},
                {"spanish": "Tokio sospechaba que Berlín ocultaba algo turbio y lo encañonó en su despacho.", "english": "Tokio suspected Berlin was hiding something shady and held him at gunpoint in his office."},
                {"spanish": "Las alianzas internas se resquebrajaban mientras las sirenas policiales no dejaban de aullar.", "english": "Internal alliances cracked as police sirens wailed relentlessly."},
                {"spanish": "El juego psicológico entre la inspectora y el Profesor se volvía cada vez más íntimo.", "english": "The psychological game between the inspector and the Professor grew increasingly intimate."},
                {"spanish": "Ninguno de los dos sabía que estaban cayendo en una trampa de sentimientos verdaderos.", "english": "Neither of them knew they were falling into a trap of genuine feelings."}
            ]
        },
        {
            "episode": "S01E05 - El día de la marmota",
            "lines": [
                {"spanish": "La rutina del encierro puede ser más peligrosa que un tiroteo a corta distancia.", "english": "The monotony of lockdown can be more dangerous than a close-range shootout."},
                {"spanish": "Las horas se repetían como en un bucle eterno donde el reloj apenas se movía.", "english": "The hours repeated like an endless loop where the clock barely ticked forward."},
                {"spanish": "Los rehenes cavaban el túnel por turnos con las manos llenas de ampollas y callos.", "english": "The hostages dug the tunnel in shifts, their hands covered in blisters and calluses."},
                {"spanish": "Alison Parker estaba hundida emocionalmente por el acoso que sufría en el colegio.", "english": "Alison Parker was devastated by the bullying she had suffered at school."},
                {"spanish": "Sus compañeros de clase habían difundido una fotografía íntima por las redes sociales.", "english": "Her classmates had circulated a private photo across social media."},
                {"spanish": "Nairobi la llevó aparte y le dio una lección de coraje que jamás olvidaría.", "english": "Nairobi took her aside and gave her an unforgettable lesson in courage."},
                {"spanish": "Mírame a los ojos, pequeña: tú eres una mujer fuerte, valiente y auténtica.", "english": "Look me in the eyes, girl: you are a strong, brave, authentic woman."},
                {"spanish": "¿Sabes cuál es mi mayor superpoder en esta vida? Que me importa un carajo lo que piensen.", "english": "Do you know what my greatest superpower in life is? That I don't give a damn what they think."},
                {"spanish": "Tienes que quererte a ti misma por encima de todos esos idiotas cobardes.", "english": "You have to love yourself above all those cowardly idiots."},
                {"spanish": "Alison levantó la cabeza y por primera vez en días sintió una chispa de dignidad.", "english": "Alison held her head high and for the first time in days felt a spark of dignity."},
                {"spanish": "Río vigilaba las cámaras de seguridad mientras escuchaba las conversaciones de la policía.", "english": "Rio monitored security feeds while eavesdropping on police communications."},
                {"spanish": "Interceptó una llamada en la que se hablaba de un rehén con problemas cardíacos.", "english": "He intercepted a call mentioning a hostage with heart conditions."},
                {"spanish": "Arturo Román fingió un ataque al corazón para provocar la entrada de los médicos de urgencia.", "english": "Arturo Román feigned a heart attack to provoke emergency paramedics to enter."},
                {"spanish": "El Profesor autorizó la entrada de un equipo quirúrgico bajo estrictas medidas de control.", "english": "The Professor authorized a surgical team's entry under strict security protocols."},
                {"spanish": "Ángel Rubio intentó infiltrarse como enfermero camuflado entre los sanitarios.", "english": "Ángel Rubio tried to infiltrate disguised as a nurse among the medics."},
                {"spanish": "El Profesor advirtió la maniobra a través de las microcámaras instaladas en las gafas.", "english": "The Professor spotted the maneuver through micro-cameras fitted in glasses."},
                {"spanish": "Berlín obligó a todos los presentes a cambiarse de mono antes de que cruzaran el umbral.", "english": "Berlin forced everyone present to swap jumpsuits before crossing the threshold."},
                {"spanish": "La policía comprobó con rabia que el caballo de Troya había sido neutralizado de nuevo.", "english": "The police discovered with fury that their Trojan horse had been neutralized once again."},
                {"spanish": "En el hangar, el Profesor recibió la visita inesperada de Raquel tras una dura jornada.", "english": "At the hangar, the Professor received an unexpected visit from Raquel after an exhausting day."},
                {"spanish": "Ella necesitaba desahogarse sobre su divorcio, su hija pequeña y su madre enferma.", "english": "She needed to vent about her divorce, her young daughter, and her ailing mother."},
                {"spanish": "El Profesor escuchaba con devoción, atrapado entre su deber criminal y su corazón.", "english": "The Professor listened with devotion, torn between criminal duty and his heart."},
                {"spanish": "Le preparó una cena sencilla y compartieron risas que parecían ajenas al asedio.", "english": "He prepared her a simple dinner and they shared laughs that seemed oblivious to the siege."},
                {"spanish": "Por unas horas, no existía ni el atraco del siglo ni la mayor operación policial de España.", "english": "For a few hours, neither the heist of the century nor Spain's biggest police operation existed."},
                {"spanish": "Solo había dos almas solitarias encontrándose en medio de una tormenta feroz.", "english": "There were only two lonely souls meeting in the middle of a fierce storm."},
                {"spanish": "Pero el amanecer devolvió la cruda realidad con la fuerza de un mazazo implacable.", "english": "Yet dawn brought back harsh reality with the force of an unyielding sledgehammer."},
                {"spanish": "Un testigo del desguace reconoció al supuesto vagabundo y acudió a comisaría.", "english": "A witness from the scrapyard recognized the supposed vagrant and went to the police."},
                {"spanish": "El retrato robot del cerebro del atraco estaba a punto de ver la luz pública.", "english": "The composite sketch of the heist mastermind was about to be made public."}
            ]
        },
        {
            "episode": "S01E06 - La cálida Guerra Fría",
            "lines": [
                {"spanish": "Un buen retrato robot en televisión puede desmantelar el plan más perfecto del mundo.", "english": "A good composite sketch on television can dismantle the most perfect plan on Earth."},
                {"spanish": "El dibujante de la policía completaba los rasgos faciales del sospechoso del desguace.", "english": "The police sketch artist was finishing the facial features of the scrapyard suspect."},
                {"spanish": "El Profesor supo que si su cara salía en los telediarios, no habría vuelta atrás.", "english": "The Professor knew that if his face hit the news broadcasts, there would be no going back."},
                {"spanish": "Interceptó la frecuencia de radio de la policía científica que custodiaba el dibujo.", "english": "He intercepted the radio frequency of the forensics team guarding the sketch."},
                {"spanish": "Se introdujo en el coche patrulla disfrazado con un uniforme reglamentario sustraído.", "english": "He slipped into the patrol car disguised in a stolen regulation uniform."},
                {"spanish": "Con una cuchilla y disolvente borró los ojos y la mandíbula del papel original.", "english": "With a blade and solvent, he wiped away the eyes and jaw from the original paper."},
                {"spanish": "El dibujo quedó inutilizable y la emisión especial de televisión tuvo que cancelarse.", "english": "The sketch was ruined and the special television broadcast had to be canceled."},
                {"spanish": "El subinspector Ángel Rubio empezó a atar cabos sueltos con sospechas crecientes.", "english": "Sub-inspector Ángel Rubio began connecting the dots with growing suspicions."},
                {"spanish": "¿Cómo es posible que los atracadores se anticipen a cada uno de nuestros pasos?", "english": "How is it possible that the robbers anticipate every single one of our steps?"},
                {"spanish": "Tiene que haber un topo en la carpa de operaciones, gritó indignado ante los mandos.", "english": "There must be a mole in the command tent, he shouted outraged before the chiefs."},
                {"spanish": "La desconfianza envenenó el ambiente entre los agentes de la policía judicial.", "english": "Distrust poisoned the atmosphere among the judicial police detectives."},
                {"spanish": "Dentro de la fábrica, la tensión estalló en un motín de consecuencias imprevisibles.", "english": "Inside the mint, tension erupted into a mutiny with unpredictable consequences."},
                {"spanish": "Tokio descubrió que Berlín padecía una enfermedad terminal degenerativa y letal.", "english": "Tokio discovered that Berlin suffered from a fatal, degenerative terminal illness."},
                {"spanish": "No le importaba morir dentro con tal de pasar a la historia como un héroe trágico.", "english": "He didn't care about dying inside as long as he went down in history as a tragic hero."},
                {"spanish": "En una acalorada discusión, Berlín ordenó atar a Tokio a una camilla con ruedas.", "english": "In a heated argument, Berlin ordered Tokio strapped to a wheeled stretcher."},
                {"spanish": "La empujó por las puertas principales y la entregó directamente a los geos armados.", "english": "He pushed her through the front doors and handed her straight to armed tactical police."},
                {"spanish": "Río presenció la traición en directo a través de los monitores de vigilancia.", "english": "Rio witnessed the betrayal live on surveillance monitors."},
                {"spanish": "Desesperado y fuera de sí, desenfundó su arma y apuntó directamente al pecho de Berlín.", "english": "Desperate and frantic, he drew his gun and aimed straight at Berlin's chest."},
                {"spanish": "Nairobi intervino con una templanza y una fuerza que nos heló la sangre a todos.", "english": "Nairobi stepped in with a poise and power that froze everyone's blood."},
                {"spanish": "Le arrebató el mando a Berlín de un golpe seco y proclamó su frase legendaria:", "english": "She seized command from Berlin with one decisive move and declared her legendary phrase:"},
                {"spanish": "A partir de ahora, señores, ¡empieza el matriarcado!", "english": "From now on, gentlemen, the matriarchy begins!"},
                {"spanish": "La autoridad cambió de manos y la disciplina volvió a imponerse en los talleres.", "english": "Authority changed hands and discipline was restored across the workshops."},
                {"spanish": "Helsinki ató a Berlín a una columna mientras Río lloraba desconsolado por Tokio.", "english": "Helsinki tied Berlin to a pillar while Rio wept inconsolably for Tokio."},
                {"spanish": "Nairobi tomó el megáfono y reorganizó la impresión a velocidad de récord nacional.", "english": "Nairobi took the megaphone and reorganized the printing at national-record speed."},
                {"spanish": "No hemos venido aquí a destruirnos entre nosotros, gritó con la voz enérgica.", "english": "We didn't come here to destroy each other, she shouted with forceful resolve."},
                {"spanish": "Hemos venido a fabricar dos mil cuatrocientos millones de euros y a salir libres.", "english": "We came to print two point four billion euros and walk out free."},
                {"spanish": "El reloj marcaba noventa horas de asedio y la resistencia demostraba su verdadero coraje.", "english": "The clock marked ninety hours of siege and the resistance showed its true courage."}
            ]
        },
        {
            "episode": "S01E07 - Refrigerada inestabilidad",
            "lines": [
                {"spanish": "Perder a un compañero de equipo te deja un vacío que ninguna fortuna puede llenar.", "english": "Losing a teammate leaves an emptiness that no fortune can ever fill."},
                {"spanish": "Tokio fue trasladada a los juzgados de plaza de Castilla bajo escolta militar blindada.", "english": "Tokio was transferred to the Plaza de Castilla courts under armored military escort."},
                {"spanish": "Durante el interrogatorio judicial no soltó una sola palabra sobre el Profesor.", "english": "During the judicial interrogation she didn't utter a single word about the Professor."},
                {"spanish": "En la fábrica, Arturo Román lideró un intento de fuga masiva con dieciséis rehenes.", "english": "Inside the mint, Arturo Román led a mass escape attempt with sixteen hostages."},
                {"spanish": "Aprovecharon el cambio de turno en la zona de carga para detonar una carga menor.", "english": "They exploited the shift change in the loading dock to detonate a small explosive."},
                {"spanish": "Helsinki y Oslo custodiaban el pasillo cuando los rehenes se abalanzaron sobre ellos.", "english": "Helsinki and Oslo were guarding the hallway when the hostages rushed them."},
                {"spanish": "Un golpe violento con una barra de hierro dejó a Oslo gravemente herido e inconsciente.", "english": "A violent strike with an iron bar left Oslo critically injured and unconscious."},
                {"spanish": "Los dieciséis rehenes lograron escapar por el boquete abierto hacia la calle trasera.", "english": "The sixteen hostages managed to escape through the opening onto the rear street."},
                {"spanish": "La fuga fue un golpe devastador para la moral del grupo y para nuestra seguridad.", "english": "The breakout was a devastating blow to our group's morale and our security."},
                {"spanish": "Helsinki lloraba sobre el cuerpo inerte de su primo, su hermano de armas en tantas guerras.", "english": "Helsinki wept over the lifeless body of his cousin, his comrade across so many wars."},
                {"spanish": "La mirada de dolor de aquel gigante conmovió incluso a los rehenes más distantes.", "english": "The giant's look of heartbreak moved even the most distant hostages."},
                {"spanish": "El Profesor recibió la noticia con un nudo en la garganta desde su centro de mando.", "english": "The Professor received the news with a lump in his throat from his command post."},
                {"spanish": "Prometió que nadie más caería y que rescataría a Tokio antes de su ingreso en prisión.", "english": "He promised nobody else would fall and that he would rescue Tokio before prison intake."},
                {"spanish": "Ideó un plan de rescate audaz en mitad del traslado penitenciario por carretera.", "english": "He devised a bold rescue operation mid-route during the highway prison transfer."},
                {"spanish": "Cuatro mercenarios serbios contratados interceptaron el furgón de la Guardia Civil.", "english": "Four hired Serbian mercenaries intercepted the Civil Guard van."},
                {"spanish": "Con granadas de humo y disparos precisos a los neumáticos liberaron a Tokio en segundos.", "english": "With smoke grenades and accurate shots to the tires, they freed Tokio in seconds."},
                {"spanish": "La subieron a una potente motocicleta deportiva y le entregaron las llaves del vehículo.", "english": "They set her onto a powerful sports motorcycle and handed her the ignition keys."},
                {"spanish": "Tokio aceleró con el corazón en un puño en dirección directa a la Fábrica de Moneda.", "english": "Tokio hit the gas with her heart in her throat, heading straight for the Royal Mint."},
                {"spanish": "Saltó la barricada policial volando por los aires sobre su moto en una escena mítica.", "english": "She cleared the police barricade soaring through the air on her bike in an iconic scene."},
                {"spanish": "Las puertas de la fábrica se abrieron un segundo para recibirla entre vítores y aplausos.", "english": "The mint doors opened for a split second to welcome her amid cheers and applause."},
                {"spanish": "Pero el tiroteo exterior alcanzó a Moscú, que cayó desplomado sobre el frío pavimento.", "english": "Yet the gunfire outside struck Moscow, who collapsed onto the cold pavement."},
                {"spanish": "Denver gritó de dolor al ver a su padre herido de gravedad en el vientre.", "english": "Denver screamed in anguish seeing his father critically wounded in the abdomen."},
                {"spanish": "La alegría del regreso de Tokio se tiñó de luto y angustia en cuestión de instantes.", "english": "The joy of Tokio's return was tinged with mourning and despair in a matter of moments."},
                {"spanish": "La victoria y la tragedia volvían a bailar juntas en el corazón de nuestro atraco.", "english": "Victory and tragedy were once again dancing together at the heart of our heist."}
            ]
        },
        {
            "episode": "S01E08 - Tú lo has pedido",
            "lines": [
                {"spanish": "Ver morir a un padre es una herida que no cicatriza jamás en la vida de un hijo.", "english": "Watching a father die is a wound that never heals in a son's life."},
                {"spanish": "Moscú agonizaba en el suelo del taller mientras Denver le sostenía la cabeza entre sollozos.", "english": "Moscow lay dying on the workshop floor as Denver held his head through sobs."},
                {"spanish": "No te vayas, papá, por favor, quédate conmigo, nos queda todo el dinero por gastar.", "english": "Don't go, Dad, please stay with me, we have all this money left to spend."},
                {"spanish": "Moscú, con una sonrisa serena y la voz entrecortada, le pidió perdón por sus errores.", "english": "Moscow, with a serene smile and broken voice, asked forgiveness for his mistakes."},
                {"spanish": "Solo quise darte una vida mejor de la que yo tuve, hijo mío, susurró con ternura.", "english": "I only wanted to give you a better life than the one I had, my son, he whispered gently."},
                {"spanish": "El Profesor pidió un cirujano a la policía a cambio de liberar a varios rehenes.", "english": "The Professor asked the police for a surgeon in exchange for releasing several hostages."},
                {"spanish": "El coronel Prieto se negó en rotundo, decidido a forzar la rendición total por asfixia.", "english": "Colonel Prieto refused outright, determined to force total surrender by asphyxiation."},
                {"spanish": "Raquel Murillo se indignó ante la crueldad táctica de sus superiores en el operativo.", "english": "Raquel Murillo was outraged by the tactical cruelty of her superiors in the operation."},
                {"spanish": "Las sospechas sobre Ángel habían llegado a un punto crítico en la investigación.", "english": "Suspicions surrounding Ángel had reached a boiling point in the investigation."},
                {"spanish": "Ángel descubrió la huella del Profesor en una cuchara del café y lo llamó desesperado.", "english": "Ángel uncovered the Professor's fingerprint on a café spoon and called him in desperation."},
                {"spanish": "Dejó ocho mensajes de voz en el contestador de Raquel antes de estrellar su vehículo.", "english": "He left eight voicemails on Raquel's answering machine before crashing his vehicle."},
                {"spanish": "El accidente de tráfico dejó al subinspector en coma profundo en el hospital de La Paz.", "english": "The road accident left the sub-inspector in a deep coma at La Paz Hospital."},
                {"spanish": "Raquel revisó los restos del coche y encontró la pista definitiva que señalaba a Salva.", "english": "Raquel examined the wreckage and found the decisive clue pointing to Salva."},
                {"spanish": "La finca de Toledo donde habíamos convivido durante cinco meses había sido localizada.", "english": "The Toledo estate where we had lived together for five months was pinpointed."},
                {"spanish": "La policía científica encontró restos de ADN, mapas del edificio y planos del túnel.", "english": "Forensic investigators found DNA traces, building maps, and tunnel blueprints."},
                {"spanish": "La identidad de todos los atracadores quedó al descubierto en las pantallas policiales.", "english": "The identities of all the robbers were exposed on police screens."},
                {"spanish": "Ya no éramos fantasmas con nombres de ciudades: teníamos rostro, apellidos e historia.", "english": "We were no longer ghosts with city names: we had faces, surnames, and histories."},
                {"spanish": "Moscú cerró los ojos para siempre rodeado por el cariño y el respeto de todos nosotros.", "english": "Moscow closed his eyes forever surrounded by the affection and respect of us all."},
                {"spanish": "Helsinki le colocó una flor de papel en el pecho mientras Denver lloraba desconsolado.", "english": "Helsinki placed a paper flower on his chest as Denver wept uncontrollably."},
                {"spanish": "Mónica abrazó a Denver con una devoción absoluta, sellando su amor en mitad del duelo.", "english": "Mónica held Denver with absolute devotion, sealing their love in the midst of grief."},
                {"spanish": "Berlín comprendió que el final se acercaba y asumió su destino con elegancia estoica.", "english": "Berlin understood the end was near and embraced his destiny with stoic elegance."},
                {"spanish": "El túnel de evacuación estaba a escasos metros de conectar con el almacén exterior.", "english": "The evacuation tunnel was just meters away from breaking through to the external hangar."},
                {"spanish": "La última batalla por la supervivencia y la libertad definitiva acababa de comenzar.", "english": "The final battle for survival and ultimate freedom had just begun."}
            ]
        },
        {
            "episode": "S01E09 - El que la sigue la consigue",
            "lines": [
                {"spanish": "El desenlace de una partida maestra requiere el sacrificio de las piezas más valiosas.", "english": "The endgame of a master match demands the sacrifice of the most valuable pieces."},
                {"spanish": "Los geos recibieron la orden definitiva de asaltar la fábrica con fuego real y granadas.", "english": "The tactical assault team received final orders to breach the mint with live ammo and grenades."},
                {"spanish": "El túnel subterráneo finalmente perforó la última pared hacia el hangar del Profesor.", "english": "The underground tunnel finally breached the last wall into the Professor's hangar."},
                {"spanish": "Mil millones de euros en billetes nuevos ya estaban cargados en camiones de transporte.", "english": "One billion euros in new banknotes was already loaded onto transport trucks."},
                {"spanish": "Denver y Mónica bajaron por el conducto secreto agarrados de la mano hacia la libertad.", "english": "Denver and Mónica descended through the secret passage holding hands toward freedom."},
                {"spanish": "Nairobi y Helsinki transportaban los últimos sacos con la satisfacción del trabajo cumplido.", "english": "Nairobi and Helsinki hauled the final bags with the pride of a job well done."},
                {"spanish": "Río y Tokio se despidieron con un beso apasionado antes de cruzar la galería subterránea.", "english": "Rio and Tokio parted with a passionate kiss before traversing the underground passage."},
                {"spanish": "Berlín decidió quedarse atrás junto a la trinchera para frenar el avance de las fuerzas especiales.", "english": "Berlin chose to stay behind at the barricade to stall the special forces' advance."},
                {"spanish": "Alguien tiene que cubrir la retirada para que todos vosotros podáis llegar al otro lado.", "english": "Someone has to cover the retreat so all of you can make it to the other side."},
                {"spanish": "Con una ametralladora pesada y cantando Bella Ciao a pleno pulmón desafió a la policía.", "english": "With a heavy machine gun and singing Bella Ciao at the top of his lungs, he defied the police."},
                {"spanish": "Su sacrificio heroico permitió sellar el túnel con explosivos plásticos antes del asalto.", "english": "His heroic sacrifice allowed the tunnel to be sealed with plastic explosives before the breach."},
                {"spanish": "Berlín cayó acribillado a balazos con una sonrisa triunfal en los labios.", "english": "Berlin fell riddled with bullets with a triumphant smile on his lips."},
                {"spanish": "El túnel voló por los aires, sepultando para siempre el acceso a los perseguidores.", "english": "The tunnel blew up into the air, forever burying the passageway from our pursuers."},
                {"spanish": "El Profesor lloró la muerte de su hermano Andrés en la soledad de su puesto de mando.", "english": "The Professor wept for the death of his brother Andrés in the solitude of his command post."},
                {"spanish": "Raquel Murillo llegó al hangar con el arma en la mano para detener al amor de su vida.", "english": "Raquel Murillo arrived at the hangar, gun in hand, to arrest the love of her life."},
                {"spanish": "Se miraron a los ojos en un silencio absoluto donde sobraban todas las palabras del mundo.", "english": "They looked into each other's eyes in total silence, where words were completely unnecessary."},
                {"spanish": "El Profesor bajó las manos y le explicó el verdadero sentido de la resistencia popular.", "english": "The Professor lowered his hands and explained the true meaning of popular resistance."},
                {"spanish": "En dos mil ocho los bancos fabricaron miles de millones de la nada y nadie fue a la cárcel.", "english": "In 2008 the banks printed billions out of thin air and nobody went to prison."},
                {"spanish": "Nosotros solo hemos fabricado nuestro propio dinero sin derramar la sangre de inocentes.", "english": "We merely manufactured our own money without shedding the blood of innocents."},
                {"spanish": "Raquel comprendió que la justicia de los hombres no siempre coincide con la ley escrita.", "english": "Raquel realized that human justice does not always align with the written law."},
                {"spanish": "Incapaz de traicionar lo que sentía, guardó su pistola y le permitió huir hacia el horizonte.", "english": "Unable to betray what she felt, she holstered her pistol and let him escape toward the horizon."},
                {"spanish": "Un año después, una postal de Palawan llegó al buzón secreto de la inspectora.", "english": "One year later, a postcard from Palawan arrived at the inspector's secret mailbox."},
                {"spanish": "Raquel cruzó medio planeta hasta encontrar al hombre de las gafas en una playa tropical.", "english": "Raquel crossed half the planet to find the man with the glasses on a tropical beach."},
                {"spanish": "La partida de ajedrez había terminado con el jaque mate más hermoso de la historia.", "english": "The chess match had concluded with the most beautiful checkmate in history."},
                {"spanish": "Habíamos vencido al sistema, habíamos recuperado el tiempo y éramos libres para siempre.", "english": "We had beaten the system, reclaimed our time, and were free forever."}
            ]
        }
    ]


def build_dataset_and_deck() -> None:
    print("Reading speech vocabulary inventory...")
    with open(FREQ_FILE, "r", encoding="utf-8") as f:
        freq_data = json.load(f)

    speech_surfaces = set(freq_data["values"].keys())
    print(f"Loaded {len(speech_surfaces)} speech inventory words.")

    episodes = get_season_1_episodes()
    all_spanish_lines = []
    for ep in episodes:
        for item in ep["lines"]:
            all_spanish_lines.append(item["spanish"])

    series_data = {
        "series_id": "la-casa-de-papel",
        "title": "La Casa de Papel",
        "language": "spanish",
        "season": 1,
        "episodes_count": len(episodes),
        "total_lines_count": len(all_spanish_lines),
        "episodes": episodes,
        "lines": all_spanish_lines  # backward compatibility for consumers expecting array of string lines
    }

    print(f"Compiled {len(episodes)} episodes with {len(all_spanish_lines)} dialogue lines.")
    with open(SERIES_JSON, "w", encoding="utf-8") as f:
        json.dump(series_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {SERIES_JSON}")

    # Build live deck
    surfaces = {}
    token_count = 0
    max_lines_per_surface = 8

    for ep in episodes:
        ep_title = ep["episode"]
        for line_obj in ep["lines"]:
            line_es = line_obj["spanish"]
            line_en = line_obj["english"]
            tokens = naive_tokens(line_es)
            token_count += len(tokens)
            for token in tokens:
                if token not in speech_surfaces:
                    continue
                if token not in surfaces:
                    surfaces[token] = {
                        "count": 0,
                        "lines": []
                    }
                entry = surfaces[token]
                entry["count"] += 1
                if len(entry["lines"]) < max_lines_per_surface:
                    if not any(ex["text"] == line_es for ex in entry["lines"]):
                        entry["lines"].append({
                            "text": line_es,
                            "english": line_en,
                            "song": ep_title,
                            "artist": "La Casa de Papel"
                        })

    matched_count = len(surfaces)
    print(f"Total tokens: {token_count}, Matched unique words: {matched_count}")
    print(f"Calculated levels (100 cards/level): {matched_count // 100 + (1 if matched_count % 100 else 0)}")

    deck = {
        "id": "live",
        "presetRevision": "season1-sample-v2",
        "sourceKind": "series",
        "playlistId": "la-casa-de-papel",
        "playlistName": "La Casa de Papel",
        "language": "spanish",
        "builtAt": datetime.now(timezone.utc).isoformat(),
        "trackCount": len(episodes),
        "lyricsTrackCount": len(episodes),
        "tokenCount": token_count,
        "matchedCount": matched_count,
        "surfaces": surfaces
    }

    with open(DECK_JSON, "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    print(f"Saved {DECK_JSON} ({matched_count} words).")


if __name__ == "__main__":
    build_dataset_and_deck()
