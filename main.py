from manim import *
from manim_presentation import *
from Owl import Owl
import random
import math
from colour import Color
import qrcode
import qrcode.image.svg


class Welcome(Slide):
    def construct(self):
        self.pause()
        owl = Owl()
        myOwl = always_redraw(owl.draw)
        self.add(myOwl)
        self.wait()
        owl.wave(self)
        self.pause()
        self.play(*owl.reset(), owl.ear_wink())


class Intro(Slide):
    caption = "Why would we want to use fixed sized block allocators?"
    title = Title(caption)
    reasons = BulletedList("No memory fragmentation",
                           "Stable runtime"
                           "Use of containers (std::list, std::map...)",
                           "Control over heap usage")

    def construct(self):
        question_text = Text(self.caption).scale(0.5)

        self.play(Write(question_text))
        self.wait()
        self.play(question_text.animate.become(self.title))
        self.wait()

        self.play(FadeIn(self.reasons))
        self.pause()


class CodeAppearAnimation(Animation):

    def __init__(self, mobject, time_to_stay=0.4, scaling_factor=.2, displacement=0.5, **kwargs):
        super().__init__(mobject, **kwargs)
        self.time_to_stay = time_to_stay
        self.scaling_factor = scaling_factor
        self.displacement = displacement
        self.mobject.initial_width = self.mobject.width
        self.mobject.starting_pos = self.mobject.get_center()

    def begin(self) -> None:
        super().begin()

    def interpolate_mobject(self, alpha: float) -> None:
        alpha = rate_functions.smooth(alpha)
        fadeInTime = 0.5 - self.time_to_stay / 2.
        fadeOutTime = 0.5 + self.time_to_stay / 2.
        normalized_alpha_fade_in = alpha / fadeInTime
        normalized_alpha_fade_out = (alpha - fadeOutTime) / (1 - fadeOutTime)
        if alpha < fadeInTime:
            self.mobject.set_opacity(alpha / fadeInTime)
            self.mobject.move_to(self.mobject.starting_pos + DOWN * self.displacement * (1 - normalized_alpha_fade_in))
            self.mobject.scale_to_fit_width(
                self.mobject.initial_width * (self.scaling_factor * (1 - normalized_alpha_fade_in) + 1))
        elif fadeInTime < alpha < fadeOutTime:
            self.mobject.set_opacity(1)
            self.mobject.scale(1)
            self.mobject.move_to(self.mobject.starting_pos)
        else:
            self.mobject.set_opacity(1 - normalized_alpha_fade_out)

    def clean_up_from_scene(self, scene: Scene) -> None:
        super().clean_up_from_scene(scene)
        scene.remove(self.mobject)


class HeapFragmentationProblem(Slide):
    title = Title("Memory Fragmentation")

    def construct(self):
        self.add(Intro.title)
        self.add(Intro.reasons)
        self.play(FadeOut(Intro.title))
        self.play(Intro.reasons.animate.become(self.title))

        self.wait()

        heap_width = 13
        heap_height = 3.5
        heap_shift = DOWN
        heap = Rectangle(width=heap_width, height=heap_height).shift(heap_shift)
        heap_caption = Text("Heap").next_to(heap, UR)
        heap_caption.shift(LEFT * heap_caption.width)
        # Initialize heap with "empty" blocks
        spacing = 0.15
        min_block_size, max_block_size = 0.7, 3
        displayed_rows = 7
        block_height = (heap_height - spacing * (displayed_rows + 1)) / displayed_rows
        start_pos_x = heap_width / 2. - spacing
        start_pos_y = heap_height / 2. - spacing
        x_pos = -start_pos_x
        y_pos = start_pos_y
        random.seed(42)
        current_row = 0
        heap_blocks = []
        while current_row < displayed_rows:
            block_width = random.random() * (max_block_size - min_block_size) + min_block_size
            if x_pos + block_width > heap_width / 2.:  # fill last block on row
                block_width = heap_width / 2. - x_pos - spacing

            heap_blocks.append(Rectangle(height=block_height, width=block_width).move_to(
                [[x_pos + block_width / 2., y_pos - block_height / 2., 0]]).shift(heap_shift))
            if x_pos + block_width > heap_width / 2. - spacing - 0.1:
                x_pos = -start_pos_x
                y_pos -= (block_height + spacing)
                current_row += 1

            else:
                x_pos += block_width + spacing

        self.play(FadeIn(heap), Write(heap_caption))

        def random_color():
            colors = [RED, BLUE, TEAL, GREEN, MAROON, PURPLE, GOLD, YELLOW]
            return random.choice(colors)

        def gen_malloc_code():
            malloc_code = Code(code="new()", language="cpp", style="monokai").next_to(heap, DR)
            malloc_code.shift(LEFT * malloc_code.width)
            return malloc_code

        def gen_free_code():
            free_code = Code(code="delete()", language="cpp", style="monokai").next_to(heap, DR)
            free_code.shift(LEFT * free_code.width)
            return free_code

        num_start_mallocs = 10
        ## Animate malloc
        runtime = 0.7

        random.seed(42)
        self.play(AnimationGroup(*[AnimationGroup(FadeIn(r.become(
            Rectangle(width=r.width, height=r.height, fill_opacity=0.5, color=random_color()).move_to(r.get_center()))),
            CodeAppearAnimation(gen_malloc_code()), run_time=runtime) for r in
            heap_blocks[:num_start_mallocs]], lag_ratio=0.8))

        filled_blocks = list(range(num_start_mallocs))
        free_blocks = []
        for i in range(10):
            if random.random() < 0.4:  # free
                idx = random.choice(filled_blocks)
                self.play(FadeOut(heap_blocks[idx]), CodeAppearAnimation(gen_free_code()),
                          run_time=runtime)
                filled_blocks.remove(idx)
                free_blocks.append(idx)
            else:
                if random.random() < 0.4 and len(free_blocks) > 0:  # use freed
                    idx = random.choice(free_blocks)
                    r = heap_blocks[idx]
                    new_width = random.random() * (r.width - min_block_size) + min_block_size
                    self.play(FadeIn(r.become(
                        Rectangle(width=new_width, height=r.height, fill_opacity=0.5, color=random_color()).move_to(
                            r.get_center() + LEFT * r.width / 2 + RIGHT * new_width / 2))),
                        CodeAppearAnimation(gen_malloc_code()), run_time=runtime)
                    filled_blocks.append(idx)
                    free_blocks.remove(idx)

                else:
                    if len(filled_blocks) > 0:  # new space
                        idx = max(filled_blocks) + 1
                        if idx < len(heap_blocks):
                            r = heap_blocks[idx]
                            self.play(FadeIn(r.become(
                                Rectangle(width=r.width, height=r.height, fill_opacity=0.5,
                                          color=random_color()).move_to(r.get_center()))),
                                CodeAppearAnimation(gen_malloc_code()), run_time=runtime)
                            filled_blocks.append(idx)

        self.pause()
        obj_fade_out = self.mobjects.copy()
        self.add(self.title)
        self.play(*[FadeOut(o) for o in obj_fade_out])

        conclusionstr = "Why is heap allocation a problem?"
        intermediate_conclusion = Text(conclusionstr)
        self.play(Write(intermediate_conclusion))
        self.play(intermediate_conclusion.animate.become(Title(conclusionstr)), FadeOut(self.title))
        self.title = Title(conclusionstr)
        reasons = BulletedList("Unpredictable heap space", "Unpredictable runtime")
        self.play(FadeIn(reasons))
        self.pause()
        self.play(FadeOut(reasons))


class Allocator(Slide):
    title = Title("The fixed sized Allocator")
    main = Text("But we can still do better!")

    def construct(self):
        self.title = HeapFragmentationProblem.title
        self.add(self.title)
        self.play(self.title.animate.become(Title("The fixed sized Allocator")))

        idea_sketch = BulletedList("Create fixed sized block pool", "recycle freed memory")
        self.play(Write(idea_sketch))
        self.pause()
        self.play(idea_sketch.animate.become(Text("Let's focus first on a single class!").scale(0.5)))
        self.pause()
        code = r"""
        class MyObj{
            int member1;
            int member2;
        };
        """

        myClassCode = Code(code=code, language="cpp", style="monokai")
        self.play(FadeIn(myClassCode), FadeOut(idea_sketch))
        self.pause()
        code2 = r"""
        class MyObj{
            int member1;
            int member2;
        public:
            void* operator new(size_t size) { 
                return _allocator.Allocate(size); 
            } 
            void operator delete(void* pObject) { 
                _allocator.Deallocate(pObject); 
            } 
            private: 
                static Allocator _allocator; 
        };
        """
        self.play(myClassCode.animate.become(Code(code=code2, language="cpp", style="monokai")))
        self.wait()
        self.pause()
        code3 = r"""
        class MyObj{
            int member1;
            int member2;
            DECLARE_ALLOCATOR 
        };
        """
        self.play(myClassCode.animate.become(Code(code=code3, language="cpp", style="monokai")))
        self.wait()
        self.pause()

        ###### Heap animation

        heap_width = 10
        heap_height = 2.5
        spacing = 0.15
        heap_shift = DOWN * 1.5 + RIGHT * 1.5
        heap = Rectangle(width=heap_width, height=heap_height).shift(heap_shift)
        heap_caption = Text("Heap").next_to(heap, UR)
        heap_caption.shift(LEFT * heap_caption.width)
        allocator_text = Text("MyObj Allocator").scale(0.5).next_to(heap, UL)
        allocator_text.shift(DOWN * (allocator_text.height + spacing * 3))
        displayed_rows = 5

        block_height = (heap_height - spacing * (displayed_rows + 1)) / displayed_rows

        self.play(myClassCode.animate.next_to(heap, UL).shift(RIGHT * myClassCode.width), FadeIn(heap),
                  FadeIn(heap_caption), Write(allocator_text))
        self.pause()

        num_entries = 5
        start_pos_x = heap_width / 2. - spacing
        start_pos_y = heap_height / 2. - spacing
        x_pos = -start_pos_x
        y_pos = start_pos_y
        heap_blocks = []
        for j in range(3):
            for i in range(num_entries):
                block_width = (heap_width - spacing) / num_entries - spacing
                heap_blocks.append(
                    Rectangle(height=block_height, width=block_width, color=GREEN_C, fill_opacity=0.5).move_to(
                        [x_pos + block_width / 2., y_pos - block_height / 2., 0]).shift(heap_shift))
                heap_blocks[-1].id = j * num_entries + i
                x_pos += block_width + spacing
                if j == 2 and i == 2:
                    break
            y_pos -= (spacing + block_height)
            x_pos = -start_pos_x
        last_block = heap_blocks[-1]
        heap_blocks.remove(last_block)

        def gen_malloc_code():
            malloc_code = Code(code="new(MyObj)", language="cpp", style="monokai").next_to(heap, DR)
            malloc_code.shift(LEFT * malloc_code.width)
            return malloc_code

        def gen_free_code():
            free_code = Code(code="delete(MyObj)", language="cpp", style="monokai").next_to(heap, DR)
            free_code.shift(LEFT * free_code.width)
            return free_code

        self.play(AnimationGroup(AnimationGroup(
            *[AnimationGroup(myClassCode.copy().animate.become(block), CodeAppearAnimation(gen_malloc_code())) for block
              in heap_blocks],
            lag_ratio=0.8),
            myClassCode.copy().animate.become(Text("...", color=GREEN_C).move_to(last_block.get_center())),
            lag_ratio=1))

        ### intermediate Cleanup
        obj_to_remove = self.mobjects.copy()
        obj_to_remove.remove(self.title)
        obj_to_remove.remove(heap)
        obj_to_remove.remove(heap_caption)
        obj_to_remove.remove(allocator_text)
        obj_to_remove.remove(myClassCode)
        self.remove(*obj_to_remove)
        self.add(*heap_blocks)
        self.add(last_block.become(Text("...", color=GREEN_C).move_to(last_block.get_center())))

        runtime = 0.7
        filled_blocks = list(range(math.floor(num_entries * 2.5)))
        free_blocks = []

        popuplist_scale = ValueTracker(0.01)

        def free_list():
            popup_list = Rectangle(width=allocator_text.width, height=3).scale(popuplist_scale.get_value()).move_to(
                allocator_text.get_center()).shift(DOWN * 2.3 * popuplist_scale.get_value())
            popup_caption = Text("free_list<MyObj>").scale(0.3).next_to(popup_list, UL)
            popup_caption.shift(RIGHT * popup_caption.width + 0.2 + spacing).shift(DOWN * popup_caption.height * 2.5)
            list_texts = []
            for idx, block in enumerate(free_blocks):
                list_texts.append(Text("[" + str(idx) + "]: " + str(block)).scale(0.3))
                list_texts.append(Line(LEFT, RIGHT).scale_to_fit_width(popup_list.width))
            if len(list_texts) > 0:
                list_texts[0].next_to(popup_list, UP).shift(DOWN * list_texts[0].height + DOWN * spacing * 3)
                for idx, txt in enumerate(list_texts):
                    if idx > 0:
                        txt.next_to(list_texts[idx - 1], DOWN)
            return VGroup(popup_list, popup_caption, *list_texts)

        free_list_obj = always_redraw(free_list)
        self.add(free_list_obj)
        self.play(popuplist_scale.animate.set_value(1))
        random.seed(42)
        for i in range(10):
            if random.random() < 0.3 and len(filled_blocks) > 0:  # free
                idx = random.choice(filled_blocks)
                r = heap_blocks[idx]
                self.play(
                    r.animate.become(Rectangle(width=r.width, height=r.height, fill_opacity=0, color=WHITE).move_to(
                        r.get_center())), CodeAppearAnimation(gen_free_code()), run_time=runtime)
                filled_blocks.remove(idx)
                free_blocks.append(idx)
            else:
                if len(free_blocks) > 0:
                    idx = free_blocks[-1]
                    r = heap_blocks[idx]
                    self.play(r.animate.become(
                        Rectangle(width=r.width, height=r.height, fill_opacity=0.5, color=GREEN_C).move_to(
                            r.get_center()),
                        CodeAppearAnimation(gen_malloc_code())), run_time=runtime)
                    filled_blocks.append(idx)
                    free_blocks.remove(idx)

        ### intermediate Cleanup
        obj_to_remove = self.mobjects.copy()
        obj_to_remove.remove(self.title)
        self.play(*[FadeOut(r) for r in obj_to_remove])


class AllocatorProblem(Slide):
    last_title = Title("How can we share this memory?")
    title = Title("The Allocator Problem")

    def construct(self):
        self.add(Allocator.title, Allocator.main)
        self.title = Allocator.main
        problem_allocator = Text(
            "The problem: \n\n\tInefficient usage of memory \n\tas it cannot be shared easily between classes").scale(
            0.5)
        self.play(FadeOut(Allocator.title), self.title.animate.become(Title("The Allocator Problem")),
                  Write(problem_allocator))
        self.wait(frozen_frame=False)
        self.play(problem_allocator.animate.shift(UL * 2))

        ###############
        heap_width = 10
        heap_height = 2.5
        spacing = 0.15
        heap_shift = DOWN * 1.5 + RIGHT * 1.5
        heap = Rectangle(width=heap_width, height=heap_height).shift(heap_shift)
        heap_caption = Text("Heap").next_to(heap, UR)
        heap_caption.shift(LEFT * heap_caption.width)
        allocator_text = Text("MyObj Allocator").scale(0.5).next_to(heap, UL)
        allocator_text.shift(DOWN * (allocator_text.height + spacing * 3))

        allocator_text2 = Text("Diff Allocator").scale(0.5).next_to(allocator_text, DOWN * 2)

        displayed_rows = 5

        block_height = (heap_height - spacing * (displayed_rows + 1)) / displayed_rows

        self.play(FadeIn(heap), FadeIn(heap_caption), Write(allocator_text), Write(allocator_text2))
        self.pause()

        num_entries = 5
        start_pos_x = heap_width / 2. - spacing
        start_pos_y = heap_height / 2. - spacing
        x_pos = -start_pos_x
        y_pos = start_pos_y
        heap_blocks = []
        c1 = GREEN_C
        c2 = BLUE_C
        c = c1
        free_idx = []
        random.seed(42)
        for j in range(displayed_rows):
            for i in range(num_entries):
                opacity = 0.5
                if random.random() < 0.5:
                    opacity = 0.
                    free_idx.append(j * i + i)

                block_width = (heap_width - spacing) / num_entries - spacing
                heap_blocks.append(
                    Rectangle(height=block_height, width=block_width, color=c, fill_opacity=opacity).move_to(
                        [x_pos + block_width / 2., y_pos - block_height / 2., 0]).shift(heap_shift))
                heap_blocks[-1].id = j * num_entries + i
                x_pos += block_width + spacing
                if j == 2 and i == 2:
                    c = c2
            y_pos -= (spacing + block_height)
            x_pos = -start_pos_x
        last_block = heap_blocks[-1]
        heap_blocks.remove(last_block)

        self.play(FadeIn(VGroup(*heap_blocks)))
        randomfill = random.choice(free_idx)
        c = c1
        if randomfill < 13:
            c = c2
        block = heap_blocks[randomfill].copy()
        block.set_opacity(0.5)
        block.fill_color = c
        self.play(FadeIn(block))

        self.wait()
        cross = Cross(block, scale_factor=1.1)
        self.play(FadeIn(Cross(block, scale_factor=1.1), rate_func=there_and_back_with_pause))
        self.play(FadeIn(Cross(block, scale_factor=1.1), rate_func=there_and_back_with_pause))
        self.play(FadeIn(cross))

        ### intermediate Cleanup
        obj_to_remove = self.mobjects.copy()
        obj_to_remove.remove(self.title)
        g = VGroup(cross, block, *heap_blocks, heap, heap_caption, allocator_text, allocator_text2, problem_allocator)

        question = Text("How can we share this memory?").scale(0.7)
        self.play(g.animate.become(question))
        self.wait(frozen_frame=False)
        self.pause()
        self.play(question.animate.become(self.last_title))
        self.wait()


class XAllocator(Slide):
    title = Title("And how can we use it now?")

    def construct(self):
        self.title = AllocatorProblem.last_title

        self.add(self.title)
        self.play(self.title.animate.become(Title("XAllocator")))
        self.wait(frozen_frame=False)

        reimpl_cap = Text("Xallocator replaces:").scale(0.7).shift(UP * 1.5).shift(LEFT * 1.5)

        reimpl_text = """
        void *xmalloc(size_t size);
        
        void xfree(void* ptr);
        
        void *xrealloc(void *ptr, size_t size);
        
        void xalloc_stats();
        
        void xalloc_destroy();
        """
        reimpl_code = Code(code=reimpl_text, language="cpp", style="monokai").shift(DOWN)
        self.play(AnimationGroup(Write(reimpl_cap), FadeIn(reimpl_code), lag_ratio=0.5))
        self.wait()
        self.pause()
        reimpl_group = VGroup(reimpl_cap, reimpl_code)

        static_caption = Text("Stack configuration:").scale(0.7).shift(UP * 2)
        xallocator_config_stack = """
        	#define MAX_ALLOCATORS	12
            #define MAX_BLOCKS		32
        
            // Create static storage for each static allocator instance
            CHAR* _allocator8 [sizeof(AllocatorPool<CHAR[8], MAX_BLOCKS>)];
            CHAR* _allocator16 [sizeof(AllocatorPool<CHAR[16], MAX_BLOCKS>)];
            CHAR* _allocator32 [sizeof(AllocatorPool<CHAR[32], MAX_BLOCKS>)];
            CHAR* _allocator64 [sizeof(AllocatorPool<CHAR[64], MAX_BLOCKS>)];
            CHAR* _allocator128 [sizeof(AllocatorPool<CHAR[128], MAX_BLOCKS>)];
            CHAR* _allocator256 [sizeof(AllocatorPool<CHAR[256], MAX_BLOCKS>)];
            CHAR* _allocator396 [sizeof(AllocatorPool<CHAR[396], MAX_BLOCKS>)];
            CHAR* _allocator512 [sizeof(AllocatorPool<CHAR[512], MAX_BLOCKS>)];
            CHAR* _allocator768 [sizeof(AllocatorPool<CHAR[768], MAX_BLOCKS>)];
            CHAR* _allocator1024 [sizeof(AllocatorPool<CHAR[1024], MAX_BLOCKS>)];
            CHAR* _allocator2048 [sizeof(AllocatorPool<CHAR[2048], MAX_BLOCKS>)];	
            CHAR* _allocator4096 [sizeof(AllocatorPool<CHAR[4096], MAX_BLOCKS>)];
        """

        heap_config_caption = Text("Heap configuration: ").scale(0.7).shift(UP * 1)
        xallocator_config_heap = """
        	#define MAX_ALLOCATORS  15
	        static Allocator* _allocators[MAX_ALLOCATORS];
	    """

        xallocator_config_stack_code = Code(code=xallocator_config_stack, language="cpp", style="monokai").scale(
            0.8).next_to(
            static_caption, DOWN)
        xallocator_config_heap_code = Code(code=xallocator_config_heap, language="cpp", style="monokai").next_to(
            heap_config_caption,
            DOWN)

        stack_config_group = VGroup(static_caption, xallocator_config_stack_code)
        heap_config_group = VGroup(heap_config_caption, xallocator_config_heap_code)
        self.play(reimpl_group.animate.become(stack_config_group))
        self.wait()
        self.pause()
        self.play(reimpl_group.animate.become(heap_config_group))

        qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
        qr.add_data('https://www.codeproject.com/Articles/1084801/Replace-malloc-free-with-a-fast-fixed-block-memory')
        qrCodeBlog = qr.make_image(fill_color="white", back_color="black")
        qrCodeBlog.save("media/images/blogqrcode.svg")
        qr_code_mobj = SVGMobject(file_name="media/images/blogqrcode.svg", fill_opacity=1, color=WHITE).next_to(
            heap_config_group, DR)
        qr_code_mobj.shift(LEFT * qr_code_mobj.width)
        more_details = Text("For more details:").scale(0.5).next_to(qr_code_mobj, LEFT)
        background_rect = Rectangle(width=qr_code_mobj.width, height=qr_code_mobj.height, color=WHITE,
                                    fill_opacity=1).move_to(qr_code_mobj.get_center())
        qr_code_group = VGroup(background_rect, qr_code_mobj, more_details)
        self.play(FadeIn(qr_code_group))
        self.wait()
        self.pause()
        self.play(FadeOut(qr_code_group), FadeOut(reimpl_group))

        # How it works?
        heap_width = 10.3
        heap_height = 3.5
        spacing = 0.15
        heap_shift = DOWN * 1.5 + RIGHT
        heap = Rectangle(width=heap_width, height=heap_height).shift(heap_shift)
        heap_caption = Text("Heap").next_to(heap, UR)
        heap_caption.shift(LEFT * heap_caption.width)
        allocator_text = Text(r"Alloc #1:").scale(0.5).next_to(heap, UL)
        allocator_text.shift(DOWN * (allocator_text.height + spacing * 3))
        alloc_text_spacing = 1.2
        allocator_text2 = Text(r"Alloc #2:").scale(0.5).next_to(allocator_text, DOWN * alloc_text_spacing)
        allocator_text3 = Text(r"Alloc #3:").scale(0.5).next_to(allocator_text2, DOWN * alloc_text_spacing)
        allocator_text4 = Text(r"Alloc #4:").scale(0.5).next_to(allocator_text3, DOWN * alloc_text_spacing)
        allocator_text5 = Text(r"...").scale(0.5).next_to(allocator_text4, DOWN * (alloc_text_spacing + 0.4))
        alloc_texts = VGroup(allocator_text, allocator_text2, allocator_text3, allocator_text4, allocator_text5)

        displayed_rows = 6

        block_height = (heap_height - spacing * (displayed_rows + 1)) / displayed_rows

        self.play(FadeIn(heap), FadeIn(heap_caption), Write(alloc_texts))
        self.pause()

        start_pos_x = heap_width / 2. - spacing
        start_pos_y = heap_height / 2. - spacing
        min_block_width = 0.6
        x_pos = -start_pos_x
        y_pos = start_pos_y
        heap_blocks = []
        free_idx = {}
        random.seed(41)
        block_width = min_block_width
        counter = 0
        for j, c in zip(range(displayed_rows), [RED_A, GREEN_A, BLUE_A, YELLOW_A, PURPLE_A]):
            num_entries = int((heap_width - spacing) / (block_width + spacing))
            free_idx[j] = []
            for i in range(num_entries):
                opacity = 0.5
                if random.random() < 0.5:
                    opacity = 0.
                    free_idx[j].append(counter)
                counter += 1
                heap_blocks.append(
                    Rectangle(height=block_height, width=block_width, color=c, fill_opacity=opacity).move_to(
                        [x_pos + block_width / 2., y_pos - block_height / 2., 0]).shift(heap_shift))
                heap_blocks[-1].id = counter
                x_pos += block_width + spacing

            y_pos -= (spacing + block_height)
            block_width *= 2
            x_pos = -start_pos_x

        self.play(FadeIn(VGroup(*heap_blocks)))

        malloc_code = Code(code="xmalloc(MyObj)", language="cpp", style="monokai").next_to(heap, UL)
        malloc_code.shift(RIGHT * malloc_code.width)
        self.play(Create(malloc_code))
        self.wait()
        newBlock = malloc_code.copy()
        selected_row = 2
        id = free_idx[selected_row][0]
        selected_block = heap_blocks[id]

        self.play(newBlock.animate.become(
            Rectangle(width=selected_block.width - min_block_width, height=selected_block.height, color=GOLD_E,
                      fill_opacity=0.5).next_to(heap,
                                                UL).shift(
                RIGHT * (selected_block.width - min_block_width))))

        for i in range(selected_row + 1):
            potential_free_block = heap_blocks[free_idx[i][0]]
            newPos = potential_free_block.get_center() + LEFT * potential_free_block.width / 2. + RIGHT * (
                    selected_block.width - min_block_width) / 2
            # ToDo shake animation (optional)
            self.play(newBlock.animate.move_to(newPos))
        # Fill selected block
        self.play(FadeOut(newBlock), FadeOut(malloc_code), selected_block.animate.become(
            Rectangle(width=selected_block.width, height=selected_block.height, fill_opacity=0.5, color=BLUE_A).move_to(
                selected_block.get_center())))

        free_idx[selected_row].remove(id)
        free_idx_list = []
        for key, value in free_idx.items():
            for v in value:
                free_idx_list.append(v)

        filled_block_ids = set(range(len(heap_blocks))).difference(set(free_idx_list))

        actual_used_memory_blocks = []
        slack_blocks = []
        random.seed(42)
        for idx in filled_block_ids:
            block = heap_blocks[idx]
            width = random.random() * 0.5 * block.width + 0.5 * block.width
            newPos = block.get_center() + LEFT * block.width / 2. + RIGHT * (width) / 2
            actual = Rectangle(height=block.height, width=width, color=GOLD_E, fill_opacity=0.5).move_to(newPos)
            actual_used_memory_blocks.append(actual)
            slack_width = block.width - width
            slack = Rectangle(height=block.height, width=slack_width, color=WHITE, fill_opacity=0.5).move_to(
                newPos + RIGHT * width / 2 + RIGHT * slack_width / 2)
            slack_blocks.append(slack)

        actual_text = Text("Actual used memory", color=GOLD_E).scale(0.5).next_to(heap, UL)
        actual_text.shift(RIGHT * actual_text.width)
        self.play(*[FadeIn(b) for b in actual_used_memory_blocks], Write(actual_text))
        self.wait()
        self.pause()

        slack_text = Text("Slack!").scale(0.5).next_to(heap, UL)
        slack_text.shift(RIGHT * slack_text.width)
        self.play(*[FadeOut(b) for b in actual_used_memory_blocks], *[FadeIn(b) for b in slack_blocks],
                  Write(slack_text), FadeOut(actual_text))
        self.wait(frozen_frame=False)
        self.pause()

        slack_mini_text = Text("Slack minimization").next_to(heap, UL)
        slack_mini_text.shift(RIGHT * slack_mini_text.width)
        alloc_obj = Text("MyObj Alloc").scale(0.4).next_to(allocator_text5, DOWN * (alloc_text_spacing + 0.5))
        x_pos = -start_pos_x
        block_width = 2
        new_blocks = []
        num_entries = int((heap_width - spacing) / (block_width + spacing))
        for i in range(num_entries):
            block = Rectangle(width=block_width, height=block_height, fill_opacity=0, color=BLUE_E).move_to(
                [x_pos + block_width / 2., y_pos - block_height / 2., 0]).shift(heap_shift)
            new_blocks.append(block)
            x_pos += block_width + spacing

        new_obj_text = Text("Add allocator for frequent objects").scale(0.5).next_to(heap, UL)
        new_obj_text.shift(RIGHT * new_obj_text.width)
        self.play(Write(new_obj_text), Write(alloc_obj), *[FadeIn(b) for b in new_blocks],
                  *[FadeOut(b) for b in slack_blocks],
                  FadeOut(slack_text))
        self.pause()

        ### intermediate Cleanup
        obj_to_remove = self.mobjects.copy()
        obj_to_remove.remove(self.title)
        self.play(*[FadeOut(r) for r in obj_to_remove])

        pros_text = Text("Memory can be shared!", color=GREEN_C).scale(0.7)
        cons_text = Text("Unused memory (Slack)!", color=RED_C).scale(0.7)
        compromise_text = Text("Compromise:\nUse Allocator & XAllocator").scale(0.7)

        self.play(FadeIn(pros_text))
        self.pause()
        self.play(pros_text.animate.scale(0.9).shift(UL * 1).shift(LEFT * 2), FadeIn(cons_text))
        self.wait()
        self.pause()
        self.play(cons_text.animate.scale(0.9).shift(UR * 1).shift(RIGHT * 2), FadeIn(compromise_text))

        textgroup = VGroup(pros_text, cons_text, compromise_text)

        string_question = "And how can we use it now?"
        self.play(textgroup.animate.become(Text(string_question).scale(0.6)))

        self.wait()
        self.pause()
        self.play(textgroup.animate.become(Title(string_question)), FadeOut(self.title))


class STLAllocator(Slide):
    title = Title(r"And how can we use it now?")

    def construct(self):
        self.title = XAllocator.title
        self.add(self.title)

        old_alloc = Text("std::allocator").scale(0.5).shift(LEFT * 2)
        old_malloc = Text("malloc").scale(0.5).next_to(old_alloc, DOWN)

        new_alloc = Text(r"stl_allocator").scale(0.5).shift(RIGHT * 2)
        new_malloc = Text("xmalloc").scale(0.5).next_to(new_alloc, DOWN)

        arrow = Arrow(start=old_alloc.get_right(), end=new_alloc.get_left(), buff=1).scale(0.5)
        allocs = VGroup(old_alloc, old_malloc, new_malloc, new_alloc, arrow)

        self.play(FadeIn(allocs))
        self.wait()
        self.pause()

        xcontainertext = Text("xcontainer:").scale(0.7)
        listContainerts = BulletedList("xlist",
                                       "xmap",
                                       "xmultimap",
                                       "xset",
                                       "xmultiset",
                                       "xqueue",
                                       ).scale(0.5).next_to(xcontainertext, DOWN)

        container_group = VGroup(xcontainertext, listContainerts)
        self.play(allocs.animate.shift(UP * 2), FadeIn(container_group))

        smart_ptr_txt = Text("Smart Pointers with:").scale(0.5).shift(RIGHT * 2)
        smart2 = Text("std::allocate_shared()").scale(0.5).next_to(smart_ptr_txt, DOWN).shift(RIGHT * 0.5)

        self.play(container_group.animate.shift(LEFT * 2), FadeIn(smart_ptr_txt), FadeIn(smart2))

        group = VGroup(smart2,smart_ptr_txt,container_group)
        self.pause()
        self.play(group.animate.become(Text("And even more good news!")))
        self.wait(2)


class TimingComparison(Slide):
    def construct(self):
        title = STLAllocator.title
        self.add(title)
        self.play(title.animate.become(Title("Time improvements")))

        time_table = Table([["std::list  ", "Global Heap", "1", "7.28 ms"],
                            ["std::list  ", "Global Heap", "2", "5.36 ms"],
                            ["std::list  ", "Global Heap", "3", "4.80 ms"],
                            ["xlist      ", "Fixed Block", "1", "8.69 ms"],
                            ["xlist      ", "Fixed Block", "2", "3.03 ms"],
                            ["xlist      ", "Fixed Block", "3", "2.93 ms"],
                            ["std::map   ", "Global Heap", "1", "44.9 ms"],
                            ["std::map   ", "Global Heap", "2", "45.3 ms"],
                            ["std::map   ", "Global Heap", "3", "40.6 ms"],
                            ["xmap       ", "Fixed Block", "1", "47.0 ms"],
                            ["xmap       ", "Fixed Block", "2", "39.2 ms"],
                            ["xmap       ", "Fixed Block", "3", "38.5 ms"],
                            ["std::string", "Global Heap", "1", "40.5 ms"],
                            ["std::string", "Global Heap", "2", "43.4 ms"],
                            ["std::string", "Global Heap", "3", "44.6 ms"],
                            ["xstring    ", "Fixed Block", "1", "39.2 ms"],
                            ["xstring    ", "Fixed Block", "2", "21.1 ms"],
                            ["xstring    ", "Fixed Block", "3", "19.8 ms"]],
                           col_labels=[Text("Container"), Text("Mode"), Text("Run"),
                                       Text("Benchmark Time (ms)")]).scale(4 / 18).shift(DOWN * 0.4)
        switch = False
        c = Color(hue=0, saturation=0.0, luminance=0.6)
        for i in range(len(time_table.get_rows())):
            for j in range(len(time_table.get_columns())):
                time_table.add_highlighted_cell((i + 1, j), color=c)
            if i % 3 == 0:
                if switch:
                    c = Color(hue=0, saturation=0.0, luminance=0.5)
                    switch = False
                else:
                    switch = True
                    c = Color(hue=0, saturation=0.0, luminance=0.1)

        self.play(FadeIn(time_table))
        self.play(time_table.animate.shift(LEFT * 2.7))

        list_cells = VGroup(time_table.get_cell((2, 4)), time_table.get_cell((7, 4)))
        brace_list = Brace(list_cells, direction=RIGHT)
        list_text = Text("list : -41%", t2c={"-41%": GREEN}).next_to(brace_list, RIGHT)
        sur_rects = []
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((3, 4)), time_table.get_cell((4, 4))), color=RED, buff=0))
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((6, 4)), time_table.get_cell((7, 4))), color=RED, buff=0))
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((9, 4)), time_table.get_cell((10, 4))), color=RED, buff=0))
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((12, 4)), time_table.get_cell((13, 4))), color=RED, buff=0))
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((15, 4)), time_table.get_cell((16, 4))), color=RED, buff=0))
        sur_rects.append(
            SurroundingRectangle(VGroup(time_table.get_cell((18, 4)), time_table.get_cell((19, 4))), color=RED, buff=0))

        map_cells = VGroup(time_table.get_cell((14, 4)), time_table.get_cell((19, 4)))
        brace_map = Brace(map_cells, direction=RIGHT)
        map_text = Text("string : -53%", t2c={"-53%": GREEN}).next_to(brace_map, RIGHT)

        string_cells = VGroup(time_table.get_cell((8, 4)), time_table.get_cell((13, 4)))
        brace_string = Brace(string_cells, direction=RIGHT)
        string_text = Text("map : -9.5%", t2c={"-9.5%": GREEN}).next_to(brace_string, RIGHT)

        self.play(*[Create(obj) for obj in
                    [brace_string, brace_list, brace_map, map_text, string_text, list_text, *sur_rects]])
        self.wait(frozen_frame=False)
        self.pause()
        all_objects_without_caption = self.mobjects.copy()
        all_objects_without_caption.remove(title)
        self.play(*[FadeOut(t) for t in all_objects_without_caption])
        self.play(title.animate.become(Title(r"Pros \& Cons")))
        self.wait(frozen_frame=False)

class Conclusion(Slide):
    def construct(self):
        self.add(Title(r"Pros \& Cons"))
        pros = Text("Pros", color=GREEN).shift(UP * 2)
        pros_bullet = BulletedList("Reuse of containers",
                                   "Less bugs",
                                   "Faster execution time",
                                   "No memory fragmentation")
        pros_bullet.next_to(pros, DOWN)
        pros_bullet.add_updater(lambda d: d.next_to(pros, DOWN))
        self.play(Write(pros), FadeIn(pros_bullet))
        self.pause()
        self.play(pros.animate.shift(LEFT * 3))
        cons = Text("Cons", color=RED).shift(UP * 2)
        cons_bullets = BulletedList("Unused memory (Slack)",
                                    "Not suited for vector",
                                    r"Not suited for different\\ sized objects", fill_opacity=1)
        cons_bullets.next_to(cons, DOWN)
        cons_bullets.add_updater(lambda d: d.next_to(cons, DOWN))
        cons.shift(RIGHT * 3.5)
        self.play(Write(cons), Write(cons_bullets))
        self.pause()
        self.wait()
